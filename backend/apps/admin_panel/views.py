from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db.models import Count, Sum
from django.utils import timezone
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from bookings.models import Booking, Payment
from bookings.serializers import BookingSerializer
from bookings.services import PaymentError, cancel_booking
from catalog.models import Actor, Event, EventCategory, Genre, Movie, Review
from cinemas.models import Cinema, Screen, Seat, Showtime
from .serializers import (
    AdminActorSerializer,
    AdminBookingSerializer,
    AdminCinemaSerializer,
    AdminEventCategorySerializer,
    AdminEventSerializer,
    AdminGenreSerializer,
    AdminMovieSerializer,
    AdminScreenSerializer,
    AdminShowtimeSerializer,
    AdminUserSerializer,
    SeatLayoutSerializer,
)


class IsAdminUser(permissions.BasePermission):
    message = "Admin access required."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)


class AdminReadWriteViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """CRUD viewset locked down to staff members."""

    permission_classes = [IsAdminUser]

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["request"] = self.request
        return ctx


# --------------------------------------------------------------------------
# Catalogue management
# --------------------------------------------------------------------------
class AdminMovieViewSet(AdminReadWriteViewSet):
    queryset = Movie.objects.prefetch_related("genres", "cast").all()
    serializer_class = AdminMovieSerializer


class AdminGenreViewSet(AdminReadWriteViewSet):
    queryset = Genre.objects.all()
    serializer_class = AdminGenreSerializer


class AdminActorViewSet(AdminReadWriteViewSet):
    queryset = Actor.objects.all()
    serializer_class = AdminActorSerializer


class AdminEventCategoryViewSet(AdminReadWriteViewSet):
    queryset = EventCategory.objects.all()
    serializer_class = AdminEventCategorySerializer


class AdminEventViewSet(AdminReadWriteViewSet):
    queryset = Event.objects.all()
    serializer_class = AdminEventSerializer


# --------------------------------------------------------------------------
# Cinemas, screens and showtimes
# --------------------------------------------------------------------------
class AdminCinemaViewSet(AdminReadWriteViewSet):
    queryset = Cinema.objects.order_by("name")
    serializer_class = AdminCinemaSerializer


class AdminScreenViewSet(AdminReadWriteViewSet):
    queryset = Screen.objects.all()
    serializer_class = AdminScreenSerializer


class AdminShowtimeViewSet(AdminReadWriteViewSet):
    queryset = Showtime.objects.select_related("screen", "movie").all()
    serializer_class = AdminShowtimeSerializer

    def update(self, request, *args, **kwargs):
        # Cancelling a show also releases all of its active locks.
        instance = self.get_object()
        partial = kwargs.pop("partial", False)
        data = request.data
        if data.get("status") == Showtime.Status.CANCELLED and instance.status != Showtime.Status.CANCELLED:
            instance.seat_locks.filter(status__in=["active", "converted"]).update(status="released")
        return super().update(request, *args, partial=partial, **kwargs)


class AdminSeatLayoutView(APIView):
    """POST /api/admin/seat-layout/ - generate seats for a screen."""

    permission_classes = [IsAdminUser]

    def post(self, request):
        serializer = SeatLayoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        screen = data["screen"]

        rows = data["rows"]
        columns = data["columns"]
        base_price = data["base_price"]
        premium_rows = data["premium_rows"]
        vip_rows = data["vip_rows"]

        Seat.objects.filter(screen=screen).delete()
        seats = []
        for r in range(rows):
            row_label = chr(ord("A") + r)
            for c in range(1, columns + 1):
                if vip_rows and r >= rows - vip_rows:
                    category = Seat.Category.VIP
                    price = base_price * Decimal("1.8")
                elif premium_rows and r >= rows - premium_rows:
                    category = Seat.Category.PREMIUM
                    price = base_price * Decimal("1.4")
                else:
                    category = Seat.Category.REGULAR
                    price = base_price
                seats.append(
                    Seat(
                        screen=screen, row=row_label, number=c, category=category,
                        base_price=price.quantize(Decimal("0.01")),
                    )
                )
        Seat.objects.bulk_create(seats)
        return Response({"detail": f"{len(seats)} seats created."})


# --------------------------------------------------------------------------
# Bookings, users and stats
# --------------------------------------------------------------------------
class AdminBookingViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAdminUser]
    serializer_class = AdminBookingSerializer
    queryset = Booking.objects.none()

    def get_queryset(self):
        return Booking.objects.select_related("user", "showtime__movie").prefetch_related("seats__seat").order_by("-created_at")

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["request"] = self.request
        return ctx


class AdminUserViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAdminUser]
    serializer_class = AdminUserSerializer
    queryset = User.objects.none()

    def get_queryset(self):
        return User.objects.prefetch_related("bookings").order_by("-date_joined")


class AdminStatsView(APIView):
    """GET /api/admin/stats/ - dashboard numbers and revenue summary."""

    permission_classes = [IsAdminUser]

    def get(self, request):
        today = timezone.localdate()
        confirmed = Booking.objects.filter(status=Booking.Status.CONFIRMED)
        revenue = confirmed.aggregate(s=Sum("total"))["s"] or 0

        today_bookings = Booking.objects.filter(
            status=Booking.Status.CONFIRMED, created_at__date=today
        ).count()

        # revenue over the last 7 days
        week_revenue = []
        from datetime import timedelta

        for offset in range(6, -1, -1):
            day = today - timedelta(days=offset)
            day_total = confirmed.filter(created_at__date=day).aggregate(s=Sum("total"))["s"] or 0
            week_revenue.append({"date": str(day), "revenue": float(day_total)})

        top_movies = (
            confirmed.values("showtime__movie__title")
            .annotate(bookings=Count("id"), revenue=Sum("total"))
            .order_by("-revenue")[:5]
        )

        return Response(
            {
                "totals": {
                    "users": User.objects.count(),
                    "movies": Movie.objects.count(),
                    "cinemas": Cinema.objects.count(),
                    "screens": Screen.objects.count(),
                    "showtimes": Showtime.objects.count(),
                    "bookings": Booking.objects.count(),
                    "confirmed_bookings": confirmed.count(),
                    "reviews": Review.objects.count(),
                    "events": Event.objects.count(),
                    "revenue": float(revenue),
                    "today_bookings": today_bookings,
                },
                "week_revenue": week_revenue,
                "top_movies": [
                    {"title": m["showtime__movie__title"], "bookings": m["bookings"], "revenue": float(m["revenue"])}
                    for m in top_movies
                ],
            }
        )
