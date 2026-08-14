from decimal import Decimal

from django.db import models
from django.utils.text import slugify

from core.models import TimeStampedModel


class Cinema(TimeStampedModel):
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=160, unique=True, blank=True)
    city = models.CharField(max_length=100, db_index=True)
    state = models.CharField(max_length=100, blank=True)
    address = models.TextField(blank=True)
    contact_number = models.CharField(max_length=20, blank=True)
    amenities = models.CharField(
        max_length=300,
        blank=True,
        help_text="Comma separated, e.g. Parking, Food Court, Recliners",
    )
    image = models.ImageField(upload_to="cinemas/", blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def amenities_list(self):
        return [a.strip() for a in self.amenities.split(",") if a.strip()]


class Screen(TimeStampedModel):
    class ScreenType(models.TextChoices):
        STANDARD = "standard", "Standard"
        IMAX = "imax", "IMAX"
        DOLBY = "dolby", "Dolby Atmos"
        PLATINUM = "platinum", "Platinum"
        SCREENX = "screenx", "ScreenX"
        VIP = "vip", "VIP Lounge"

    cinema = models.ForeignKey(Cinema, on_delete=models.CASCADE, related_name="screens")
    name = models.CharField(max_length=80)
    screen_type = models.CharField(
        max_length=20, choices=ScreenType.choices, default=ScreenType.STANDARD
    )
    rows = models.PositiveIntegerField(default=10, help_text="Number of seat rows")
    columns = models.PositiveIntegerField(default=12, help_text="Seats per row")

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["cinema", "name"], name="unique_screen_name_per_cinema")
        ]

    def __str__(self):
        return f"{self.cinema.name} - {self.name} ({self.get_screen_type_display()})"


class Seat(models.Model):
    class Category(models.TextChoices):
        REGULAR = "regular", "Regular"
        PREMIUM = "premium", "Premium"
        VIP = "vip", "VIP"

    screen = models.ForeignKey(Screen, on_delete=models.CASCADE, related_name="seats")
    row = models.CharField(max_length=2)
    number = models.PositiveIntegerField()
    category = models.CharField(
        max_length=10, choices=Category.choices, default=Category.REGULAR, db_index=True
    )
    base_price = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    class Meta:
        ordering = ["row", "number"]
        constraints = [
            models.UniqueConstraint(
                fields=["screen", "row", "number"], name="unique_seat_in_screen"
            )
        ]

    def __str__(self):
        return f"{self.screen} - {self.row}{self.number}"

    @property
    def label(self):
        return f"{self.row}{self.number}"


class Showtime(TimeStampedModel):
    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "Scheduled"
        RUNNING = "running", "Running"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    screen = models.ForeignKey(Screen, on_delete=models.CASCADE, related_name="showtimes")
    movie = models.ForeignKey("catalog.Movie", on_delete=models.CASCADE, related_name="showtimes")
    show_date = models.DateField(db_index=True)
    start_time = models.TimeField()
    end_time = models.TimeField()
    base_price = models.DecimalField(max_digits=8, decimal_places=2, default=200)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.SCHEDULED, db_index=True
    )

    class Meta:
        ordering = ["show_date", "start_time"]
        constraints = [
            models.UniqueConstraint(
                fields=["screen", "show_date", "start_time"], name="unique_showtime_in_screen"
            )
        ]

    def __str__(self):
        return f"{self.movie.title} @ {self.screen} {self.show_date} {self.start_time}"

    def price_for(self, seat):
        """Per-seat price based on the seat's category and the show's base price."""
        multipliers = {"regular": Decimal("1.0"), "premium": Decimal("1.4"), "vip": Decimal("1.8")}
        mult = multipliers.get(seat.category, Decimal("1.0"))
        return (self.base_price * mult).quantize(Decimal("0.01"))
