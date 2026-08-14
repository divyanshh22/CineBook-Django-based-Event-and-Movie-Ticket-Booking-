import django_filters
from django.db.models import Count
from rest_framework import filters, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from bookings.services import seat_map
from .models import Cinema, Screen, Seat, Showtime
from .serializers import CinemaSerializer, ScreenSerializer, SeatSerializer, ShowtimeSerializer


class CinemaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Cinema.objects.annotate(screen_count=Count("screens")).filter(is_active=True).order_by("name")
    serializer_class = CinemaSerializer
    lookup_field = "slug"
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["city"]
    search_fields = ["name", "city", "address"]
    permission_classes = [permissions.AllowAny]


class ScreenViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Screen.objects.annotate(seat_count=Count("seats")).select_related("cinema").all()
    serializer_class = ScreenSerializer
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_fields = ["cinema"]
    permission_classes = [permissions.AllowAny]


class SeatViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Seat.objects.all()
    serializer_class = SeatSerializer
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_fields = ["screen"]
    permission_classes = [permissions.AllowAny]


class ShowtimeFilter(django_filters.FilterSet):
    movie = django_filters.NumberFilter(field_name="movie_id")
    cinema = django_filters.NumberFilter(field_name="screen__cinema_id")
    date = django_filters.DateFilter(field_name="show_date")
    city = django_filters.CharFilter(field_name="screen__cinema__city", lookup_expr="iexact")

    class Meta:
        model = Showtime
        fields = []


class ShowtimeViewSet(viewsets.ReadOnlyModelViewSet):
    """Showtimes for movies/cinemas with the live seat map attached."""

    queryset = Showtime.objects.select_related("screen__cinema", "movie").filter(
        status__in=[Showtime.Status.SCHEDULED, Showtime.Status.RUNNING]
    )
    serializer_class = ShowtimeSerializer
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = ShowtimeFilter
    ordering_fields = ["show_date", "start_time"]
    permission_classes = [permissions.AllowAny]

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["request"] = self.request
        return ctx

    @action(detail=True, methods=["get"])
    def seats(self, request, pk=None):
        showtime = self.get_object()
        return Response(seat_map(showtime, request.user if request.user.is_authenticated else None))
