from rest_framework.routers import DefaultRouter

from .views import CinemaViewSet, ScreenViewSet, SeatViewSet, ShowtimeViewSet

router = DefaultRouter()
router.register("cinemas", CinemaViewSet)
router.register("screens", ScreenViewSet)
router.register("seats", SeatViewSet)
router.register("showtimes", ShowtimeViewSet)

urlpatterns = router.urls
