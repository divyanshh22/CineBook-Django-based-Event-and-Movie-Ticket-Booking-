from datetime import timedelta
from decimal import Decimal

from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from bookings.models import Booking, BookingSeat, Payment, SeatLock
from core.testutils import make_cinema, make_movie, make_screen, make_seats, make_showtime, make_user


class BookingFlowTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = make_user()
        self.movie = make_movie()
        self.cinema = make_cinema()
        self.screen = make_screen(self.cinema)
        self.seats = make_seats(self.screen, base_price=Decimal("200"))
        self.showtime = make_showtime(self.movie, self.screen)
        self.client.force_login(self.user)

    def seat_ids(self, n=2):
        return [s.id for s in self.seats[:n]]

    def test_seat_map_marks_everything_available(self):
        r = self.client.get(f"/api/showtimes/{self.showtime.id}/seats/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        states = {s["state"] for s in r.data}
        self.assertEqual(states, {"available"})
        self.assertEqual(len(r.data), len(self.seats))

    def test_lock_seats_creates_lock(self):
        r = self.client.post("/api/bookings/lock/", {"showtime": self.showtime.id, "seat_ids": self.seat_ids()}, format="json")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertIn("token", r.data)
        lock = SeatLock.objects.get(token=r.data["token"])
        self.assertEqual(lock.status, SeatLock.Status.ACTIVE)
        self.assertEqual(lock.seats.count(), 2)

    def test_same_user_relocks_same_seats_reuses_lock(self):
        first = self.client.post("/api/bookings/lock/", {"showtime": self.showtime.id, "seat_ids": self.seat_ids()}, format="json")
        second = self.client.post("/api/bookings/lock/", {"showtime": self.showtime.id, "seat_ids": self.seat_ids()}, format="json")
        self.assertEqual(first.data["token"], second.data["token"])

    def test_conflicting_user_cannot_lock_same_seat(self):
        ids = self.seat_ids()
        self.client.post("/api/bookings/lock/", {"showtime": self.showtime.id, "seat_ids": ids}, format="json")

        other = make_user("bob")
        other_client = APIClient()
        other_client.force_login(other)
        r = other_client.post("/api/bookings/lock/", {"showtime": self.showtime.id, "seat_ids": ids}, format="json")
        self.assertEqual(r.status_code, status.HTTP_409_CONFLICT)

    def test_seat_shows_locked_for_other_users(self):
        ids = self.seat_ids()
        self.client.post("/api/bookings/lock/", {"showtime": self.showtime.id, "seat_ids": ids}, format="json")

        other = make_user("bob")
        other_client = APIClient()
        other_client.force_login(other)
        r = other_client.get(f"/api/showtimes/{self.showtime.id}/seats/")
        locked = [s for s in r.data if s["state"] == "locked"]
        self.assertEqual(len(locked), len(ids))

    def test_booked_seat_not_available_again(self):
        ids = self.seat_ids()
        lock_r = self.client.post("/api/bookings/lock/", {"showtime": self.showtime.id, "seat_ids": ids}, format="json")
        pay_r = self.client.post("/api/payments/process/", {"lock_token": lock_r.data["token"]}, format="json")
        self.assertEqual(pay_r.status_code, status.HTTP_201_CREATED)

        other = make_user("bob")
        other_client = APIClient()
        other_client.force_login(other)
        r = other_client.post("/api/bookings/lock/", {"showtime": self.showtime.id, "seat_ids": ids}, format="json")
        self.assertEqual(r.status_code, status.HTTP_409_CONFLICT)

    def test_full_payment_flow_creates_confirmed_booking(self):
        ids = self.seat_ids()
        lock_r = self.client.post("/api/bookings/lock/", {"showtime": self.showtime.id, "seat_ids": ids}, format="json")
        pay_r = self.client.post("/api/payments/process/", {"lock_token": lock_r.data["token"]}, format="json")
        self.assertEqual(pay_r.status_code, status.HTTP_201_CREATED)

        booking = Booking.objects.get(booking_code=pay_r.data["booking"]["booking_code"])
        self.assertEqual(booking.status, Booking.Status.CONFIRMED)
        self.assertEqual(booking.seats.count(), 2)
        self.assertEqual(booking.payment.status, Payment.Status.PAID)
        lock = SeatLock.objects.get(token=lock_r.data["token"])
        self.assertEqual(lock.status, SeatLock.Status.CONVERTED)

        # total = subtotal + fee(30) + 18% tax
        subtotal = Decimal("200") * 2
        expected_total = (subtotal + Decimal("30")) * Decimal("1.18")
        self.assertAlmostEqual(booking.total, expected_total.quantize(Decimal("0.01")))

    def test_failed_payment_releases_seats(self):
        from unittest.mock import patch

        ids = self.seat_ids()
        lock_r = self.client.post("/api/bookings/lock/", {"showtime": self.showtime.id, "seat_ids": ids}, format="json")
        with patch("bookings.services.MockPaymentGateway.charge", return_value={"success": False, "transaction_id": ""}):
            pay_r = self.client.post("/api/payments/process/", {"lock_token": lock_r.data["token"]}, format="json")
        self.assertEqual(pay_r.status_code, status.HTTP_402_PAYMENT_REQUIRED)

        lock = SeatLock.objects.get(token=lock_r.data["token"])
        self.assertEqual(lock.status, SeatLock.Status.RELEASED)

        other = make_user("bob")
        other_client = APIClient()
        other_client.force_login(other)
        r = other_client.post("/api/bookings/lock/", {"showtime": self.showtime.id, "seat_ids": ids}, format="json")
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_expired_lock_is_released(self):
        ids = self.seat_ids()
        lock_r = self.client.post("/api/bookings/lock/", {"showtime": self.showtime.id, "seat_ids": ids}, format="json")
        SeatLock.objects.filter(token=lock_r.data["token"]).update(
            expires_at=timezone.now() - timedelta(minutes=1)
        )

        other = make_user("bob")
        other_client = APIClient()
        other_client.force_login(other)
        r = other_client.post("/api/bookings/lock/", {"showtime": self.showtime.id, "seat_ids": ids}, format="json")
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_payment_with_expired_lock_rejected(self):
        ids = self.seat_ids()
        lock_r = self.client.post("/api/bookings/lock/", {"showtime": self.showtime.id, "seat_ids": ids}, format="json")
        SeatLock.objects.filter(token=lock_r.data["token"]).update(
            expires_at=timezone.now() - timedelta(minutes=5)
        )
        r = self.client.post("/api/payments/process/", {"lock_token": lock_r.data["token"]}, format="json")
        self.assertEqual(r.status_code, status.HTTP_409_CONFLICT)

    def test_payment_requires_auth(self):
        anon = APIClient()
        r = anon.post("/api/payments/process/", {"lock_token": "x"}, format="json")
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_lock_requires_auth(self):
        anon = APIClient()
        r = anon.post("/api/bookings/lock/", {"showtime": self.showtime.id, "seat_ids": self.seat_ids()}, format="json")
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_bookings_list_only_mine(self):
        ids = self.seat_ids()
        lock_r = self.client.post("/api/bookings/lock/", {"showtime": self.showtime.id, "seat_ids": ids}, format="json")
        self.client.post("/api/payments/process/", {"lock_token": lock_r.data["token"]}, format="json")

        other = make_user("bob")
        other_client = APIClient()
        other_client.force_login(other)
        r = other_client.get("/api/bookings/")
        self.assertEqual(r.data["count"], 0)

        r2 = self.client.get("/api/bookings/")
        self.assertEqual(r2.data["count"], 1)

    def test_cancel_booking_releases_seats(self):
        ids = self.seat_ids()
        lock_r = self.client.post("/api/bookings/lock/", {"showtime": self.showtime.id, "seat_ids": ids}, format="json")
        pay_r = self.client.post("/api/payments/process/", {"lock_token": lock_r.data["token"]}, format="json")
        code = pay_r.data["booking"]["booking_code"]

        cancel_r = self.client.post(f"/api/bookings/{code}/cancel/")
        self.assertEqual(cancel_r.status_code, status.HTTP_200_OK)

        booking = Booking.objects.get(booking_code=code)
        self.assertEqual(booking.status, Booking.Status.CANCELLED)
        self.assertEqual(booking.payment.status, Payment.Status.REFUNDED)

        other = make_user("bob")
        other_client = APIClient()
        other_client.force_login(other)
        r = other_client.post("/api/bookings/lock/", {"showtime": self.showtime.id, "seat_ids": ids}, format="json")
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_ticket_download(self):
        ids = self.seat_ids()
        lock_r = self.client.post("/api/bookings/lock/", {"showtime": self.showtime.id, "seat_ids": ids}, format="json")
        pay_r = self.client.post("/api/payments/process/", {"lock_token": lock_r.data["token"]}, format="json")
        code = pay_r.data["booking"]["booking_code"]

        r = self.client.get(f"/api/bookings/{code}/ticket/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r["Content-Type"], "image/png")

    def test_ticket_download_denied_for_other_user(self):
        ids = self.seat_ids()
        lock_r = self.client.post("/api/bookings/lock/", {"showtime": self.showtime.id, "seat_ids": ids}, format="json")
        pay_r = self.client.post("/api/payments/process/", {"lock_token": lock_r.data["token"]}, format="json")
        code = pay_r.data["booking"]["booking_code"]

        other = make_user("bob")
        other_client = APIClient()
        other_client.force_login(other)
        r = other_client.get(f"/api/bookings/{code}/ticket/")
        self.assertEqual(r.status_code, status.HTTP_404_NOT_FOUND)

    def test_booking_detail_denied_for_other_user(self):
        ids = self.seat_ids()
        lock_r = self.client.post("/api/bookings/lock/", {"showtime": self.showtime.id, "seat_ids": ids}, format="json")
        pay_r = self.client.post("/api/payments/process/", {"lock_token": lock_r.data["token"]}, format="json")
        code = pay_r.data["booking"]["booking_code"]

        other = make_user("bob")
        other_client = APIClient()
        other_client.force_login(other)
        r = other_client.get(f"/api/bookings/{code}/")
        self.assertEqual(r.status_code, status.HTTP_404_NOT_FOUND)

    def test_cancel_non_confirmed_booking_rejected(self):
        ids = self.seat_ids()
        lock_r = self.client.post("/api/bookings/lock/", {"showtime": self.showtime.id, "seat_ids": ids}, format="json")
        pay_r = self.client.post("/api/payments/process/", {"lock_token": lock_r.data["token"]}, format="json")
        code = pay_r.data["booking"]["booking_code"]

        # cancel once, then cancelling again must fail
        self.client.post(f"/api/bookings/{code}/cancel/")
        r = self.client.post(f"/api/bookings/{code}/cancel/")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unknown_payment_method_is_rejected_not_500(self):
        ids = self.seat_ids()
        lock_r = self.client.post("/api/bookings/lock/", {"showtime": self.showtime.id, "seat_ids": ids}, format="json")
        r = self.client.post(
            "/api/payments/process/",
            {"lock_token": lock_r.data["token"], "method": "bitcoin"},
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_409_CONFLICT)
        self.assertIn("Unknown payment method", str(r.data["detail"]))

    def test_max_10_seats_per_booking(self):
        ids = [s.id for s in self.seats[:11]]
        r = self.client.post("/api/bookings/lock/", {"showtime": self.showtime.id, "seat_ids": ids}, format="json")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_duplicate_seat_ids_rejected(self):
        ids = [self.seats[0].id, self.seats[0].id]
        r = self.client.post("/api/bookings/lock/", {"showtime": self.showtime.id, "seat_ids": ids}, format="json")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_price_preview(self):
        ids = self.seat_ids(2)
        r = self.client.post("/api/bookings/price/", {"showtime": self.showtime.id, "seat_ids": ids}, format="json")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(len(r.data["seats"]), 2)
        self.assertEqual(r.data["price"]["subtotal"], Decimal("400.00"))

    def test_price_preview_invalid_seat_rejected(self):
        from cinemas.models import Seat

        other_screen = make_screen(make_cinema("Other", city="Delhi"))
        bad = Seat.objects.create(
            screen=other_screen, row="Z", number=99, category=Seat.Category.REGULAR, base_price=Decimal("200")
        )
        r = self.client.post(
            "/api/bookings/price/",
            {"showtime": self.showtime.id, "seat_ids": [bad.id]},
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_booking_filter_upcoming_past(self):
        ids = self.seat_ids()
        lock_r = self.client.post("/api/bookings/lock/", {"showtime": self.showtime.id, "seat_ids": ids}, format="json")
        self.client.post("/api/payments/process/", {"lock_token": lock_r.data["token"]}, format="json")

        # showtime is tomorrow -> upcoming
        r = self.client.get("/api/bookings/", {"filter": "upcoming"})
        self.assertEqual(r.data["count"], 1)
        r = self.client.get("/api/bookings/", {"filter": "past"})
        self.assertEqual(r.data["count"], 0)

        # move show into the past -> past
        from django.db.models import DateField, ExpressionWrapper
        from django.db.models.functions import Now
        from cinemas.models import Showtime

        Showtime.objects.filter(pk=self.showtime.pk).update(show_date=(timezone.now() - timedelta(days=2)).date())
        r = self.client.get("/api/bookings/", {"filter": "upcoming"})
        self.assertEqual(r.data["count"], 0)
        r = self.client.get("/api/bookings/", {"filter": "past"})
        self.assertEqual(r.data["count"], 1)
