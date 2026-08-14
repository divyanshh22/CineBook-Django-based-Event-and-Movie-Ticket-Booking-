"""Booking business logic: seat locking, confirmation and payments.

Race conditions (two users grabbing the same seat) are handled by running
conflict checks inside a database transaction while holding row locks on the
Seat rows themselves, ordered by id to avoid deadlocks.
"""
import secrets
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from cinemas.models import Showtime
from .models import CONVENIENCE_FEE, Booking, BookingSeat, Payment, SeatLock, TAX_RATE


class LockError(Exception):
    """Raised when seats cannot be locked."""


class PaymentError(Exception):
    """Raised when a payment cannot be processed."""


def _lock_ttl_minutes():
    return int(getattr(settings, "SEAT_LOCK_TTL_MINUTES", 10))


def _generate_token():
    return secrets.token_urlsafe(16)[:24]


def expire_stale_locks(showtime):
    """Release locks that have outlived their TTL (lazy cleanup)."""
    stale = SeatLock.objects.filter(
        showtime=showtime, status=SeatLock.Status.ACTIVE, expires_at__lt=timezone.now()
    )
    stale.update(status=SeatLock.Status.EXPIRED)


def _conflicting_booking_seats(showtime, seat_ids):
    """Seats that already belong to a confirmed booking for this show."""
    return set(
        BookingSeat.objects.filter(
            booking__showtime=showtime,
            booking__status=Booking.Status.CONFIRMED,
            seat_id__in=seat_ids,
        ).values_list("seat_id", flat=True)
    )


def _active_locks_for_seats(showtime, seat_ids, exclude_user=None):
    """Active (unexpired) locks held by *other* users on the given seats."""
    qs = (
        SeatLock.objects.filter(
            showtime=showtime,
            status=SeatLock.Status.ACTIVE,
            expires_at__gt=timezone.now(),
            seats__id__in=seat_ids,
        )
        .distinct()
        .prefetch_related("seats")
    )
    if exclude_user is not None:
        qs = qs.exclude(user=exclude_user)
    return list(qs)


def lock_seats(user, showtime_id, seat_ids, ttl_minutes=None):
    """Temporarily hold seats for a user so no one else can book them.

    Returns (lock, error_message). An already-existing active lock owned by
    the same user is reused; any other conflicting hold or confirmed booking
    makes the whole request fail.
    """
    ttl_minutes = ttl_minutes or _lock_ttl_minutes()

    try:
        showtime = Showtime.objects.select_related("screen__cinema", "movie").get(pk=showtime_id)
    except Showtime.DoesNotExist:
        raise LockError("Showtime not found.")

    if showtime.status == Showtime.Status.CANCELLED:
        raise LockError("This show has been cancelled.")

    seat_ids = list(dict.fromkeys(int(i) for i in seat_ids))
    if not seat_ids:
        raise LockError("No seats selected.")

    # Pull the seat rows for locking; this is what serialises concurrent
    # attempts so a seat can't be double-booked.
    seats = list(showtime.screen.seats.filter(id__in=seat_ids).select_for_update().order_by("id"))
    if len(seats) != len(seat_ids):
        raise LockError("One or more seats do not belong to this show.")

    with transaction.atomic():
        expire_stale_locks(showtime)

        # The same user re-selecting the same seats can keep their existing lock.
        existing = (
            SeatLock.objects.filter(user=user, showtime=showtime, status=SeatLock.Status.ACTIVE)
            .filter(expires_at__gt=timezone.now())
            .first()
        )
        if existing and set(existing.seats.values_list("id", flat=True)) == set(seat_ids):
            existing.expires_at = timezone.now() + timezone.timedelta(minutes=ttl_minutes)
            existing.save(update_fields=["expires_at", "updated_at"])
            return existing, None

        # Drop any other lock the user holds on this show, then check for
        # conflicts with other people.
        SeatLock.objects.filter(user=user, showtime=showtime, status=SeatLock.Status.ACTIVE).update(
            status=SeatLock.Status.RELEASED
        )

        booked = _conflicting_booking_seats(showtime, seat_ids)
        if booked:
            labels = [f"{s.row}{s.number}" for s in seats if s.id in booked]
            raise LockError(f"Seat(s) {', '.join(labels)} already booked.")

        conflicting = _active_locks_for_seats(showtime, seat_ids, exclude_user=user)
        if conflicting:
            raise LockError("One or more selected seats are not available right now.")

        lock = SeatLock.objects.create(
            showtime=showtime,
            user=user,
            token=_generate_token(),
            expires_at=timezone.now() + timezone.timedelta(minutes=ttl_minutes),
        )
        lock.seats.set(seats)
        return lock, None


def seat_map(showtime, user=None):
    """Availability snapshot of every seat for a showtime.

    Each entry carries the seat's state from this user's perspective:
    available / booked / locked / mine.
    """
    expire_stale_locks(showtime)

    booked_ids = set(
        BookingSeat.objects.filter(
            booking__showtime=showtime, booking__status=Booking.Status.CONFIRMED
        ).values_list("seat_id", flat=True)
    )
    all_seat_ids = list(showtime.screen.seats.values_list("id", flat=True))
    locked = _active_locks_for_seats(showtime, all_seat_ids)

    mine_ids, locked_ids = set(), set()
    for lock in locked:
        seat_ids = {s.id for s in lock.seats.all()}
        if user and lock.user_id == user.id:
            mine_ids.update(seat_ids)
        else:
            locked_ids.update(seat_ids)

    rows = []
    for seat in showtime.screen.seats.select_related("screen").all():
        if seat.id in booked_ids:
            state = "booked"
        elif seat.id in locked_ids:
            state = "locked"
        elif seat.id in mine_ids:
            state = "mine"
        else:
            state = "available"
        rows.append(
            {
                "id": seat.id,
                "label": seat.label,
                "row": seat.row,
                "number": seat.number,
                "category": seat.category,
                "price": showtime.price_for(seat),
                "state": state,
            }
        )
    return rows


def price_breakdown(showtime, seats):
    """Subtotal + convenience fee + tax + total for a set of seats."""
    subtotal = sum((showtime.price_for(s) for s in seats), Decimal("0.00"))
    convenience = CONVENIENCE_FEE
    tax = (subtotal + convenience) * TAX_RATE
    total = subtotal + convenience + tax
    return {
        "subtotal": subtotal.quantize(Decimal("0.01")),
        "convenience_fee": convenience.quantize(Decimal("0.01")),
        "tax": tax.quantize(Decimal("0.01")),
        "total": total.quantize(Decimal("0.01")),
    }


# --------------------------------------------------------------------------
# Payments
# --------------------------------------------------------------------------
class PaymentGateway:
    """Base class. Swap in a real gateway (Razorpay/Stripe) later."""

    id = "base"

    def charge(self, amount, order_reference):
        raise NotImplementedError


class MockPaymentGateway(PaymentGateway):
    """Development gateway. Succeeds unless the amount ends in .99 or the
    order reference contains 'fail' — handy for testing the failure path."""

    id = "mock"

    def charge(self, amount, order_reference):
        import random

        failed = str(amount).endswith(".99") or "fail" in order_reference.lower()
        if failed:
            return {"success": False, "transaction_id": ""}
        return {"success": True, "transaction_id": "TXN-" + secrets.token_hex(6).upper()}


class RazorpayGateway(PaymentGateway):
    id = "razorpay"

    def charge(self, amount, order_reference):
        raise NotImplementedError("Razorpay integration pending. Add keys and implement.")


class StripeGateway(PaymentGateway):
    id = "stripe"

    def charge(self, amount, order_reference):
        raise NotImplementedError("Stripe integration pending. Add keys and implement.")


GATEWAYS = {
    "mock": MockPaymentGateway,
    "razorpay": RazorpayGateway,
    "stripe": StripeGateway,
}


def get_gateway(method=None):
    gateway_name = (method or getattr(settings, "PAYMENT_GATEWAY", "mock")).lower()
    gateway_class = GATEWAYS.get(gateway_name)
    if gateway_class is None:
        raise PaymentError(f"Unknown payment method: {gateway_name or 'none'}.")
    return gateway_class()


def process_payment(user, lock_token, method=None):
    """Complete the booking once payment succeeds.

    Returns a dict {booking, payment, success, error}.
    """
    gateway = get_gateway(method)

    try:
        lock = (
            SeatLock.objects.select_for_update()
            .select_related("showtime__screen__cinema", "showtime__movie")
            .get(token=lock_token)
        )
    except SeatLock.DoesNotExist:
        raise PaymentError("Invalid seat lock.")

    if lock.user_id != user.id:
        raise PaymentError("This seat lock does not belong to you.")

    if lock.status != SeatLock.Status.ACTIVE:
        raise PaymentError("This seat lock is no longer active.")

    if lock.is_expired():
        lock.release()
        raise PaymentError("Your seats were released. Please select again.")

    seats = list(lock.seats.all())
    breakdown = price_breakdown(lock.showtime, seats)

    # Create the booking and payment records first (both pending).
    with transaction.atomic():
        booking = Booking.objects.create(
            user=user,
            showtime=lock.showtime,
            subtotal=breakdown["subtotal"],
            convenience_fee=breakdown["convenience_fee"],
            tax=breakdown["tax"],
            total=breakdown["total"],
            status=Booking.Status.PENDING,
        )
        BookingSeat.objects.bulk_create(
            [BookingSeat(booking=booking, seat=s, price=lock.showtime.price_for(s)) for s in seats]
        )
        payment = Payment.objects.create(
            booking=booking, amount=booking.total, status=Payment.Status.PENDING, method=gateway.id
        )

    # Call the gateway outside the transaction.
    result = gateway.charge(payment.amount, booking.booking_code)

    with transaction.atomic():
        payment = Payment.objects.select_for_update().get(pk=payment.pk)
        booking = Booking.objects.select_for_update().get(pk=booking.pk)
        lock = SeatLock.objects.select_for_update().get(pk=lock.pk)

        if result["success"]:
            payment.status = Payment.Status.PAID
            payment.gateway_transaction_id = result.get("transaction_id", "")
            payment.paid_at = timezone.now()
            booking.status = Booking.Status.CONFIRMED
            lock.status = SeatLock.Status.CONVERTED
            payment.save()
            booking.save(update_fields=["status", "updated_at"])
            lock.save(update_fields=["status", "updated_at"])
            return {"success": True, "booking": booking, "payment": payment, "lock": lock}

        payment.status = Payment.Status.FAILED
        booking.status = Booking.Status.CANCELLED
        lock.status = SeatLock.Status.RELEASED
        payment.save()
        booking.save(update_fields=["status", "updated_at"])
        lock.save(update_fields=["status", "updated_at"])
        return {"success": False, "booking": booking, "payment": payment, "lock": lock}


def cancel_booking(user, booking_code):
    """Admin/user cancellation. Releases seats and records the refund state."""
    try:
        booking = Booking.objects.select_for_update().get(
            booking_code=booking_code, user=user
        )
    except Booking.DoesNotExist:
        raise PaymentError("Booking not found.")

    if booking.status != Booking.Status.CONFIRMED:
        raise PaymentError("Only confirmed bookings can be cancelled.")

    with transaction.atomic():
        booking.status = Booking.Status.CANCELLED
        booking.save(update_fields=["status", "updated_at"])
        if hasattr(booking, "payment") and booking.payment.status == Payment.Status.PAID:
            booking.payment.status = Payment.Status.REFUNDED
            booking.payment.save(update_fields=["status", "updated_at"])
    return booking
