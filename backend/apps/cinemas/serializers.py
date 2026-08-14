from decimal import Decimal

from rest_framework import serializers

from .models import Cinema, Screen, Seat, Showtime


class CinemaSerializer(serializers.ModelSerializer):
    amenities_list = serializers.ReadOnlyField()
    screen_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Cinema
        fields = [
            "id", "name", "slug", "city", "state", "address", "contact_number",
            "amenities", "amenities_list", "image", "is_active", "screen_count",
        ]


class ScreenSerializer(serializers.ModelSerializer):
    cinema_name = serializers.CharField(source="cinema.name", read_only=True)
    screen_type_display = serializers.CharField(source="get_screen_type_display", read_only=True)
    seat_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Screen
        fields = [
            "id", "cinema", "cinema_name", "name", "screen_type", "screen_type_display",
            "rows", "columns", "seat_count",
        ]


class SeatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Seat
        fields = ["id", "screen", "row", "number", "label", "category", "base_price"]


class ShowtimeSerializer(serializers.ModelSerializer):
    movie = serializers.StringRelatedField()
    movie_id = serializers.IntegerField(source="movie.id", read_only=True)
    movie_poster = serializers.SerializerMethodField()
    screen_name = serializers.CharField(source="screen.name", read_only=True)
    screen_type = serializers.CharField(source="screen.screen_type", read_only=True)
    screen_type_display = serializers.CharField(source="screen.get_screen_type_display", read_only=True)
    cinema = serializers.CharField(source="screen.cinema.name", read_only=True)
    cinema_id = serializers.IntegerField(source="screen.cinema.id", read_only=True)
    city = serializers.CharField(source="screen.cinema.city", read_only=True)
    prices = serializers.SerializerMethodField()
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Showtime
        fields = [
            "id", "movie", "movie_id", "movie_poster", "screen", "screen_name",
            "screen_type", "screen_type_display", "cinema", "cinema_id", "city",
            "show_date", "start_time", "end_time", "base_price", "prices",
            "status", "status_display",
        ]

    def get_movie_poster(self, obj):
        request = self.context.get("request")
        if obj.movie.poster and request:
            return request.build_absolute_uri(obj.movie.poster.url)
        return None

    def get_prices(self, obj):
        multipliers = {"regular": Decimal("1.0"), "premium": Decimal("1.4"), "vip": Decimal("1.8")}
        return {
            cat: str((obj.base_price * mult).quantize(Decimal("0.01")))
            for cat, mult in multipliers.items()
        }
