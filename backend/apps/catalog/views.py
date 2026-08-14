import django_filters
from django.db.models import Avg, Count, Q
from django.utils import timezone
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Actor, Event, EventCategory, Genre, Movie, Review
from .serializers import (
    ActorSerializer,
    EventCategorySerializer,
    EventSerializer,
    GenreSerializer,
    MovieDetailSerializer,
    MovieListSerializer,
    ReviewSerializer,
)


class MovieFilter(django_filters.FilterSet):
    genre = django_filters.CharFilter(field_name="genres__slug", lookup_expr="exact")
    language = django_filters.CharFilter(lookup_expr="iexact")
    min_rating = django_filters.NumberFilter(method="filter_min_rating")
    status = django_filters.CharFilter(field_name="status", lookup_expr="exact")
    trending = django_filters.BooleanFilter()

    class Meta:
        model = Movie
        fields = []

    def filter_min_rating(self, queryset, name, value):
        return queryset.annotate(avg=Avg("reviews__rating")).filter(avg__gte=value)


class MovieViewSet(viewsets.ReadOnlyModelViewSet):
    """Public catalogue of movies, filterable by genre, language and rating."""

    queryset = Movie.objects.all()
    lookup_field = "slug"
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = MovieFilter
    search_fields = ["title", "description", "director", "cast__name", "genres__name"]
    ordering_fields = ["release_date", "title", "duration", "avg_rating"]
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = super().get_queryset().distinct().select_related().prefetch_related("genres", "cast")
        qs = qs.annotate(avg_rating=Avg("reviews__rating"), review_count=Count("reviews", distinct=True))
        ordering = self.request.query_params.get("ordering")
        if ordering == "popularity":
            qs = qs.order_by("-trending", "-avg_rating", "-release_date")
        return qs

    def get_serializer_class(self):
        if self.action == "retrieve":
            return MovieDetailSerializer
        return MovieListSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data
        # attach showtimes grouped by date for convenience (future shows only)
        now = timezone.localtime()
        showtimes = (
            instance.showtimes.select_related("screen__cinema")
            .filter(
                status__in=["scheduled", "running"],
            )
            .exclude(
                Q(show_date__lt=now.date())
                | Q(show_date=now.date(), start_time__lt=now.time())
            )
            .order_by("show_date", "start_time")
        )
        dates = {}
        for st in showtimes:
            key = str(st.show_date)
            dates.setdefault(key, []).append(
                {
                    "id": st.id,
                    "time": st.start_time.strftime("%H:%M"),
                    "end_time": st.end_time.strftime("%H:%M"),
                    "cinema_id": st.screen.cinema_id,
                    "cinema": st.screen.cinema.name,
                    "city": st.screen.cinema.city,
                    "screen_id": st.screen_id,
                    "screen": st.screen.name,
                    "screen_type": st.screen.screen_type,
                    "base_price": str(st.base_price),
                }
            )
        data["showtimes_by_date"] = dates
        return Response(data)


class GenreViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Genre.objects.annotate(movie_count=Count("movies", distinct=True))
    serializer_class = GenreSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["name"]
    permission_classes = [permissions.AllowAny]


class ActorViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Actor.objects.all()
    serializer_class = ActorSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["name"]
    permission_classes = [permissions.AllowAny]


class EventCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = EventCategory.objects.annotate(event_count=Count("events", distinct=True))
    serializer_class = EventCategorySerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["name"]
    permission_classes = [permissions.AllowAny]


class EventFilter(django_filters.FilterSet):
    category = django_filters.CharFilter(field_name="category__slug", lookup_expr="exact")
    city = django_filters.CharFilter(lookup_expr="iexact")
    status = django_filters.CharFilter(field_name="status", lookup_expr="exact")

    class Meta:
        model = Event
        fields = []


class EventViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Event.objects.select_related("category").all()
    serializer_class = EventSerializer
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = EventFilter
    search_fields = ["title", "description", "venue", "city"]
    ordering_fields = ["starts_at"]
    permission_classes = [permissions.AllowAny]


class ReviewViewSet(viewsets.ModelViewSet):
    """Reviews for movies. Users can create one review per movie."""

    queryset = Review.objects.select_related("user", "movie").all()
    serializer_class = ReviewSerializer

    def get_permissions(self):
        if self.action in ["create"]:
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def get_queryset(self):
        qs = self.queryset
        movie = self.request.query_params.get("movie")
        if movie:
            qs = qs.filter(movie_id=movie)
        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
