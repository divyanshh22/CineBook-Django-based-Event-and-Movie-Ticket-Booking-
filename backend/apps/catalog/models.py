from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.text import slugify

from core.models import TimeStampedModel


class Genre(models.Model):
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Actor(models.Model):
    name = models.CharField(max_length=150)
    photo = models.ImageField(upload_to="actors/", blank=True, null=True)
    bio = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Movie(TimeStampedModel):
    """A feature film listed in the catalogue."""

    class Status(models.TextChoices):
        NOW_SHOWING = "now_showing", "Now showing"
        UPCOMING = "upcoming", "Upcoming"
        ARCHIVED = "archived", "Archived"

    title = models.CharField(max_length=200, db_index=True)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField(blank=True)
    poster = models.ImageField(upload_to="posters/", blank=True, null=True)
    backdrop = models.ImageField(upload_to="backdrops/", blank=True, null=True)
    trailer_url = models.URLField(blank=True)

    duration = models.PositiveIntegerField(help_text="Duration in minutes")
    release_date = models.DateField(db_index=True)
    language = models.CharField(max_length=60, db_index=True)
    certification = models.CharField(max_length=10, blank=True, help_text="e.g. U, U/A, A")
    director = models.CharField(max_length=150, blank=True)

    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.NOW_SHOWING, db_index=True
    )
    trending = models.BooleanField(default=False, db_index=True)

    genres = models.ManyToManyField(Genre, related_name="movies", blank=True)
    cast = models.ManyToManyField(Actor, related_name="movies", blank=True)

    class Meta:
        ordering = ["-release_date"]
        indexes = [models.Index(fields=["status", "-release_date"])]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def average_rating(self):
        agg = self.reviews.aggregate(avg=models.Avg("rating"), count=models.Count("id"))
        return {
            "average": round(agg["avg"], 1) if agg["avg"] else None,
            "count": agg["count"],
        }


class EventCategory(models.Model):
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Event(TimeStampedModel):
    class Status(models.TextChoices):
        LIVE = "live", "Live"
        UPCOMING = "upcoming", "Upcoming"
        ENDED = "ended", "Ended"

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField(blank=True)
    poster = models.ImageField(upload_to="event_posters/", blank=True, null=True)
    category = models.ForeignKey(
        EventCategory, on_delete=models.SET_NULL, null=True, related_name="events"
    )
    venue = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=100, db_index=True)
    starts_at = models.DateTimeField(db_index=True)
    ends_at = models.DateTimeField()
    ticket_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.UPCOMING)

    class Meta:
        ordering = ["starts_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)


class Review(TimeStampedModel):
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="reviews")
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name="reviews")
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["user", "movie"], name="one_review_per_user_per_movie")
        ]

    def __str__(self):
        return f"{self.user.username} - {self.movie.title} ({self.rating}/5)"
