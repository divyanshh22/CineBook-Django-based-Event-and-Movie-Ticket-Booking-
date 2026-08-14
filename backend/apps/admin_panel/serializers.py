from rest_framework import serializers

from accounts.models import User
from bookings.models import Booking
from catalog.models import Actor, Event, EventCategory, Genre, Movie, Review
from cinemas.models import Cinema, Screen, Seat, Showtime


class AdminMovieSerializer(serializers.ModelSerializer):
    genre_ids = serializers.PrimaryKeyRelatedField(
        source="genres", queryset=Genre.objects.all(), many=True, required=False
    )
    cast_ids = serializers.PrimaryKeyRelatedField(
        source="cast", queryset=Actor.objects.all(), many=True, required=False
    )

    class Meta:
        model = Movie
        fields = [
            "id", "title", "slug", "description", "poster", "backdrop", "trailer_url",
            "duration", "release_date", "language", "certification", "director",
            "status", "trending", "genre_ids", "cast_ids",
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["genres"] = [g.name for g in instance.genres.all()]
        data["cast"] = [a.name for a in instance.cast.all()]
        return data


class AdminGenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ["id", "name", "slug"]


class AdminActorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Actor
        fields = ["id", "name", "bio", "photo"]


class AdminCinemaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cinema
        fields = [
            "id", "name", "slug", "city", "state", "address", "contact_number",
            "amenities", "image", "is_active",
        ]


class AdminScreenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Screen
        fields = ["id", "cinema", "name", "screen_type", "rows", "columns"]


class AdminSeatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Seat
        fields = ["id", "screen", "row", "number", "category", "base_price"]


class SeatLayoutSerializer(serializers.Serializer):
    """Bulk-define a screen's seat layout."""

    screen = serializers.PrimaryKeyRelatedField(queryset=Screen.objects.all())
    rows = serializers.IntegerField(min_value=1, max_value=26)
    columns = serializers.IntegerField(min_value=1, max_value=30)
    base_price = serializers.DecimalField(max_digits=8, decimal_places=2)
    premium_rows = serializers.IntegerField(default=0, help_text="Last N rows are premium")
    vip_rows = serializers.IntegerField(default=0, help_text="Last N rows are VIP (overrides premium)")


class AdminShowtimeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Showtime
        fields = [
            "id", "screen", "movie", "show_date", "start_time", "end_time",
            "base_price", "status",
        ]


class AdminBookingSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    movie = serializers.CharField(source="showtime.movie.title", read_only=True)
    show_date = serializers.DateField(source="showtime.show_date", read_only=True)
    start_time = serializers.TimeField(source="showtime.start_time", read_only=True)
    seats = serializers.SerializerMethodField()
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Booking
        fields = [
            "id", "booking_code", "username", "movie", "show_date", "start_time",
            "subtotal", "convenience_fee", "tax", "total", "status", "status_display",
            "seats", "created_at",
        ]

    def get_seats(self, obj):
        return [bs.seat.label for bs in obj.seats.all()]


class AdminUserSerializer(serializers.ModelSerializer):
    booking_count = serializers.SerializerMethodField()
    spent = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id", "username", "email", "phone_number", "first_name", "last_name",
            "is_staff", "is_active", "date_joined", "booking_count", "spent",
        ]

    def get_booking_count(self, obj):
        return obj.bookings.filter(status=Booking.Status.CONFIRMED).count()

    def get_spent(self, obj):
        from django.db.models import Sum

        return obj.bookings.filter(status=Booking.Status.CONFIRMED).aggregate(
            s=Sum("total")
        )["s"] or 0


class AdminEventCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = EventCategory
        fields = ["id", "name", "slug"]


class AdminEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = [
            "id", "title", "slug", "description", "poster", "category", "venue",
            "city", "starts_at", "ends_at", "ticket_price", "status",
        ]
