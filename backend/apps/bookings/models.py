import secrets
import string
from decimal import Decimal

from django.db import models

from core.models import TimeStampedModel

CONVENIENCE_FEE = Decimal("30.00")
TAX_RATE = Decimal("0.18")


def generate_booking_code():
    alphabet = string.ascii_uppercase + string.digits
    return "CB-" + "".join(secrets.choice(alphabet) for _ in range(8))


class SeatLock(TimeStampedModel):
    """A temporary hold on seats while a user completes payment.

    Created when seats are selected, released on expiry/payment failure,
    and converted into a real booking after a successful payment.
    """

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        CONVERTED = "converted", "Converted"
        RELEASED = "released", "Released"
        EXPIRED = "expired", "Expired"

    showtime = models.ForeignKey("cinemas.Showtime", on_delete=models.CASCADE, related_name="seat_locks")
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="seat_locks")
    token = models.CharField(max_length=32, unique=True, db_index=True)
    seats = models.ManyToManyField("cinemas.Seat")
    expires_at = models.DateTimeField(db_index=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.ACTIVE, db_index=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Lock {self.token} ({self.status})"

    def is_expired(self, now=None):
        from django.utils import timezone

        return (now or timezone.now()) >= self.expires_at

    def release(self):
        self.status = self.Status.EXPIRED if self.is_expired() else self.Status.RELEASED
        self.save(update_fields=["status", "updated_at"])


class Booking(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = "confirmed", "Confirmed"
        CANCELLED = "cancelled", "Cancelled"

    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="bookings")
    showtime = models.ForeignKey("cinemas.Showtime", on_delete=models.CASCADE, related_name="bookings")
    booking_code = models.CharField(max_length=16, unique=True, default=generate_booking_code)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    convenience_fee = models.DecimalField(max_digits=10, decimal_places=2, default=CONVENIENCE_FEE)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.CONFIRMED, db_index=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.booking_code} - {self.user.username}"

    def calculate_totals(self, subtotal):
        convenience = self.convenience_fee
        tax = (subtotal + convenience) * TAX_RATE
        self.subtotal = subtotal
        self.convenience_fee = convenience
        self.tax = tax.quantize(Decimal("0.01"))
        self.total = (subtotal + convenience + self.tax).quantize(Decimal("0.01"))


class BookingSeat(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="seats")
    seat = models.ForeignKey("cinemas.Seat", on_delete=models.CASCADE, related_name="booking_entries")
    price = models.DecimalField(max_digits=8, decimal_places=2)

    class Meta:
        ordering = ["seat__row", "seat__number"]
        constraints = [
            models.UniqueConstraint(fields=["booking", "seat"], name="unique_booking_seat"),
        ]

    def __str__(self):
        return f"{self.booking.booking_code} - {self.seat.label}"


class Payment(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PAID = "paid", "Paid"
        FAILED = "failed", "Failed"
        REFUNDED = "refunded", "Refunded"

    class Method(models.TextChoices):
        MOCK = "mock", "Mock gateway"
        STRIPE = "stripe", "Stripe"
        RAZORPAY = "razorpay", "Razorpay"

    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name="payment")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING, db_index=True)
    method = models.CharField(max_length=10, choices=Method.choices, default=Method.MOCK)
    gateway_transaction_id = models.CharField(max_length=100, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.booking.booking_code} - {self.status}"
