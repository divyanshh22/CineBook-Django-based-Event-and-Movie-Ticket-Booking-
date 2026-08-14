from rest_framework import serializers

from .models import Booking, BookingSeat, Payment, SeatLock


class SeatDetailSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    label = serializers.CharField()
    row = serializers.CharField()
    number = serializers.IntegerField()
    category = serializers.CharField()
    price = serializers.CharField()
    state = serializers.CharField()


class LockSeatsSerializer(serializers.Serializer):
    showtime = serializers.IntegerField()
    seat_ids = serializers.ListField(child=serializers.IntegerField())

    def validate_seat_ids(self, value):
        if not value:
            raise serializers.ValidationError("Select at least one seat.")
        if len(value) > 10:
            raise serializers.ValidationError("Maximum 10 seats per booking.")
        if len(set(value)) != len(value):
            raise serializers.ValidationError("Duplicate seats selected.")
        return value


class BookingSeatSerializer(serializers.ModelSerializer):
    seat = serializers.CharField(source="seat.label", read_only=True)
    category = serializers.CharField(source="seat.category", read_only=True)

    class Meta:
        model = BookingSeat
        fields = ["seat", "category", "price"]


class BookingSerializer(serializers.ModelSerializer):
    seats = BookingSeatSerializer(many=True, read_only=True)
    movie = serializers.CharField(source="showtime.movie.title", read_only=True)
    movie_poster = serializers.SerializerMethodField()
    cinema = serializers.CharField(source="showtime.screen.cinema.name", read_only=True)
    cinema_city = serializers.CharField(source="showtime.screen.cinema.city", read_only=True)
    screen = serializers.CharField(source="showtime.screen.name", read_only=True)
    screen_type = serializers.CharField(source="showtime.screen.screen_type", read_only=True)
    show_date = serializers.DateField(source="showtime.show_date", read_only=True)
    start_time = serializers.TimeField(source="showtime.start_time", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    payment_status = serializers.CharField(source="payment.status", read_only=True)

    class Meta:
        model = Booking
        fields = [
            "id", "booking_code", "user", "showtime", "movie", "movie_poster",
            "cinema", "cinema_city", "screen", "screen_type", "show_date",
            "start_time", "subtotal", "convenience_fee", "tax", "total",
            "status", "status_display", "payment_status", "seats", "created_at",
        ]
        read_only_fields = ["user"]

    def get_movie_poster(self, obj):
        request = self.context.get("request")
        if obj.showtime.movie.poster and request:
            return request.build_absolute_uri(obj.showtime.movie.poster.url)
        return None


class PaymentStatusSerializer(serializers.Serializer):
    lock_token = serializers.CharField()


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ["id", "amount", "status", "method", "gateway_transaction_id", "paid_at"]
