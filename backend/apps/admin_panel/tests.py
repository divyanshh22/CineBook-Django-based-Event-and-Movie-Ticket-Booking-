from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from accounts.models import User
from cinemas.models import Cinema
from core.testutils import make_cinema, make_movie, make_screen, make_user


class AdminPermissionTests(APITestCase):
    def setUp(self):
        self.staff = User.objects.create_user(username="boss", email="boss@test.local", password="Str0ng!Pass123", is_staff=True)
        self.user = make_user()

    def test_admin_endpoints_reject_regular_users(self):
        self.client.force_login(self.user)
        for url in ["/api/admin/stats/", "/api/admin/movies/", "/api/admin/cinemas/", "/api/admin/bookings/", "/api/admin/users/"]:
            r = self.client.get(url)
            self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN, url)

    def test_admin_endpoints_require_login(self):
        r = self.client.get("/api/admin/stats/")
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_stats_for_staff(self):
        self.client.force_login(self.staff)
        r = self.client.get("/api/admin/stats/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertIn("totals", r.data)
        self.assertIn("week_revenue", r.data)

    def test_movie_crud_for_staff(self):
        self.client.force_login(self.staff)
        r = self.client.post(
            "/api/admin/movies/",
            {"title": "Admin Movie", "duration": 100, "release_date": "2026-01-01", "language": "English", "status": "upcoming"},
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        movie_id = r.data["id"]
        r2 = self.client.patch(f"/api/admin/movies/{movie_id}/", {"trending": True}, format="json")
        self.assertEqual(r2.status_code, status.HTTP_200_OK)
        r3 = self.client.delete(f"/api/admin/movies/{movie_id}/")
        self.assertEqual(r3.status_code, status.HTTP_204_NO_CONTENT)

    def test_seat_layout_generation(self):
        self.client.force_login(self.staff)
        cinema = make_cinema()
        screen = make_screen(cinema, rows=5, columns=6)
        r = self.client.post(
            "/api/admin/seat-layout/",
            {"screen": screen.id, "rows": 5, "columns": 6, "base_price": "200", "premium_rows": 1, "vip_rows": 0},
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        screen.refresh_from_db()
        self.assertEqual(screen.seats.count(), 30)

    def test_showtime_cancel_releases_locks(self):
        from bookings.models import SeatLock

        self.client.force_login(self.staff)
        from core.testutils import make_seats, make_showtime

        movie = make_movie()
        cinema = make_cinema()
        screen = make_screen(cinema)
        make_seats(screen)
        showtime = make_showtime(movie, screen)

        # user locks a seat
        user_client = APIClient()
        user_client.force_login(self.user)
        seat = screen.seats.first()
        lock_r = user_client.post("/api/bookings/lock/", {"showtime": showtime.id, "seat_ids": [seat.id]}, format="json")
        lock = SeatLock.objects.get(token=lock_r.data["token"])
        self.assertEqual(lock.status, SeatLock.Status.ACTIVE)

        r = self.client.patch(
            f"/api/admin/showtimes/{showtime.id}/",
            {"status": "cancelled"},
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        lock.refresh_from_db()
        self.assertEqual(lock.status, SeatLock.Status.RELEASED)

    def test_cinema_crud_for_staff(self):
        from catalog.models import Event, EventCategory
        from cinemas.models import Screen

        self.client.force_login(self.staff)

        # create cinema
        r = self.client.post(
            "/api/admin/cinemas/",
            {"name": "PVR Phoenix", "city": "Mumbai", "address": "Lower Parel"},
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        cinema_id = r.data["id"]

        # create screen
        r = self.client.post(
            "/api/admin/screens/",
            {"cinema": cinema_id, "name": "Screen 1", "screen_type": "standard", "rows": 4, "columns": 5},
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

        # update cinema
        r = self.client.patch(f"/api/admin/cinemas/{cinema_id}/", {"is_active": False}, format="json")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertFalse(r.data["is_active"])

        # delete cinema
        r = self.client.delete(f"/api/admin/cinemas/{cinema_id}/")
        self.assertEqual(r.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Cinema.objects.filter(pk=cinema_id).exists())

    def test_screen_crud_for_staff(self):
        from cinemas.models import Screen

        self.client.force_login(self.staff)
        cinema = make_cinema()
        r = self.client.post(
            "/api/admin/screens/",
            {"cinema": cinema.id, "name": "IMAX 1", "screen_type": "imax", "rows": 6, "columns": 8},
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        screen_id = r.data["id"]

        r = self.client.patch(f"/api/admin/screens/{screen_id}/", {"rows": 8}, format="json")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data["rows"], 8)

    def test_genre_crud_for_staff(self):
        self.client.force_login(self.staff)
        r = self.client.post("/api/admin/genres/", {"name": "Sci-Fi"}, format="json")
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        genre_id = r.data["id"]

        r = self.client.patch(f"/api/admin/genres/{genre_id}/", {"name": "SciFi"}, format="json")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data["name"], "SciFi")

        r = self.client.delete(f"/api/admin/genres/{genre_id}/")
        self.assertEqual(r.status_code, status.HTTP_204_NO_CONTENT)

    def test_event_and_category_crud_for_staff(self):
        from datetime import timedelta

        from django.utils import timezone

        from catalog.models import Event, EventCategory

        self.client.force_login(self.staff)

        r = self.client.post("/api/admin/event-categories/", {"name": "Theatre"}, format="json")
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        cat_id = r.data["id"]

        r = self.client.post(
            "/api/admin/events/",
            {
                "title": "Hamlet Live",
                "category": cat_id,
                "venue": "NCPA",
                "city": "Mumbai",
                "starts_at": (timezone.now() + timedelta(days=3)).isoformat(),
                "ends_at": (timezone.now() + timedelta(days=3, hours=3)).isoformat(),
                "ticket_price": "800.00",
            },
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        event_id = r.data["id"]

        r = self.client.patch(f"/api/admin/events/{event_id}/", {"status": "live"}, format="json")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data["status"], "live")
