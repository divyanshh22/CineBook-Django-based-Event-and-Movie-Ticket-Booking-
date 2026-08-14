from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    AdminActorViewSet,
    AdminBookingViewSet,
    AdminCinemaViewSet,
    AdminEventCategoryViewSet,
    AdminEventViewSet,
    AdminGenreViewSet,
    AdminMovieViewSet,
    AdminScreenViewSet,
    AdminSeatLayoutView,
    AdminShowtimeViewSet,
    AdminStatsView,
    AdminUserViewSet,
)

router = DefaultRouter()
router.register("movies", AdminMovieViewSet)
router.register("genres", AdminGenreViewSet)
router.register("actors", AdminActorViewSet)
router.register("cinemas", AdminCinemaViewSet)
router.register("screens", AdminScreenViewSet)
router.register("showtimes", AdminShowtimeViewSet)
router.register("bookings", AdminBookingViewSet)
router.register("users", AdminUserViewSet)
router.register("events", AdminEventViewSet)
router.register("event-categories", AdminEventCategoryViewSet)

urlpatterns = [
    path("seat-layout/", AdminSeatLayoutView.as_view(), name="seat-layout"),
    path("stats/", AdminStatsView.as_view(), name="stats"),
] + router.urls
