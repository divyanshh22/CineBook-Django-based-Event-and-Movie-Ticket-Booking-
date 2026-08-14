from rest_framework.routers import DefaultRouter

from .views import ActorViewSet, EventCategoryViewSet, EventViewSet, GenreViewSet, MovieViewSet, ReviewViewSet

router = DefaultRouter()
router.register("movies", MovieViewSet)
router.register("genres", GenreViewSet)
router.register("actors", ActorViewSet)
router.register("events", EventViewSet)
router.register("event-categories", EventCategoryViewSet)
router.register("reviews", ReviewViewSet)

urlpatterns = router.urls
