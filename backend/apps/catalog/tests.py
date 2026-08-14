from datetime import date, timedelta

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from core.testutils import give_review, make_genre, make_movie, make_user
from catalog.models import Event, EventCategory

User = get_user_model()


class MovieFilterTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.action = make_genre("Action")
        self.drama = make_genre("Drama")
        self.m1 = make_movie("Alpha Film", status="now_showing", release_date=date.today() - timedelta(days=10))
        self.m1.genres.add(self.action)
        self.m2 = make_movie("Beta Flick", status="upcoming", release_date=date.today() + timedelta(days=20))
        self.m2.genres.add(self.drama)

    def test_list_movies(self):
        r = self.client.get("/api/movies/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data["count"], 2)

    def test_filter_by_genre(self):
        r = self.client.get("/api/movies/", {"genre": "action"})
        self.assertEqual(r.data["count"], 1)
        self.assertEqual(r.data["results"][0]["title"], "Alpha Film")

    def test_filter_by_status(self):
        r = self.client.get("/api/movies/", {"status": "upcoming"})
        self.assertEqual(r.data["count"], 1)
        self.assertEqual(r.data["results"][0]["title"], "Beta Flick")

    def test_search_by_title(self):
        r = self.client.get("/api/movies/", {"search": "alpha"})
        self.assertEqual(r.data["count"], 1)

    def test_min_rating_filter(self):
        user = make_user()
        give_review(user, self.m1, rating=5)
        r = self.client.get("/api/movies/", {"min_rating": 4.5})
        self.assertEqual(r.data["count"], 1)
        self.assertEqual(r.data["results"][0]["title"], "Alpha Film")

    def test_ordering_by_release_date(self):
        r = self.client.get("/api/movies/", {"ordering": "release_date"})
        titles = [m["title"] for m in r.data["results"]]
        # Alpha released 3 days ago, Beta is upcoming (released in future via defaults)
        self.assertEqual(titles[0], "Alpha Film")

    def test_detail_includes_cast_and_genres(self):
        user = make_user()
        give_review(user, self.m1, rating=5)
        r = self.client.get(f"/api/movies/{self.m1.slug}/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data["genres"][0]["name"], "Action")
        self.assertIn("showtimes_by_date", r.data)


class ReviewTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = make_user()
        self.movie = make_movie()

    def test_create_review_requires_auth(self):
        r = self.client.post("/api/reviews/", {"movie": self.movie.id, "rating": 4}, format="json")
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_review(self):
        self.client.force_login(self.user)
        r = self.client.post("/api/reviews/", {"movie": self.movie.id, "rating": 5, "comment": "Loved it"}, format="json")
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertEqual(r.data["user"], self.user.username)

    def test_one_review_per_user(self):
        self.client.force_login(self.user)
        self.client.post("/api/reviews/", {"movie": self.movie.id, "rating": 5}, format="json")
        r = self.client.post("/api/reviews/", {"movie": self.movie.id, "rating": 3}, format="json")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reject_invalid_rating(self):
        self.client.force_login(self.user)
        r = self.client.post("/api/reviews/", {"movie": self.movie.id, "rating": 9}, format="json")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)


class EventTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.category = EventCategory.objects.create(name="Music")
        from datetime import timedelta
        from django.utils import timezone

        self.event = Event.objects.create(
            title="Sunburn Goa",
            category=self.category,
            venue="Beach Stage",
            city="Goa",
            starts_at=timezone.now() + timedelta(days=5),
            ends_at=timezone.now() + timedelta(days=6),
            ticket_price="1200.00",
            status=Event.Status.UPCOMING,
        )

    def test_list_events(self):
        r = self.client.get("/api/events/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data["count"], 1)
        self.assertEqual(r.data["results"][0]["category"], "Music")

    def test_filter_events_by_city(self):
        Event.objects.create(
            title="Comedy Night", venue="Club", city="Mumbai",
            starts_at=self.event.starts_at, ends_at=self.event.ends_at,
        )
        r = self.client.get("/api/events/", {"city": "goa"})
        self.assertEqual(r.data["count"], 1)
        self.assertEqual(r.data["results"][0]["title"], "Sunburn Goa")

    def test_search_events_by_title(self):
        r = self.client.get("/api/events/", {"search": "sunburn"})
        self.assertEqual(r.data["count"], 1)

    def test_event_categories_have_counts(self):
        r = self.client.get("/api/event-categories/")
        self.assertEqual(r.data["count"], 1)
        self.assertEqual(r.data["results"][0]["event_count"], 1)
