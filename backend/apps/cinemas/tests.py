from datetime import date, time, timedelta

from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from core.testutils import make_cinema, make_movie, make_screen, make_seats, make_showtime


class CinemaShowtimeTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.movie = make_movie()
        self.cinema = make_cinema()
        self.screen = make_screen(self.cinema)
        self.seats = make_seats(self.screen)
        self.showtime = make_showtime(self.movie, self.screen)

    def test_list_cinemas(self):
        r = self.client.get("/api/cinemas/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data["count"], 1)

    def test_cinema_filter_by_city(self):
        make_cinema("Other", city="Delhi")
        r = self.client.get("/api/cinemas/", {"city": "Delhi"})
        self.assertEqual(r.data["count"], 1)

    def test_showtime_filter_by_date(self):
        r = self.client.get("/api/showtimes/", {"date": self.showtime.show_date})
        self.assertEqual(r.data["count"], 1)

    def test_showtime_filter_by_movie(self):
        r = self.client.get("/api/showtimes/", {"movie": self.movie.id})
        self.assertEqual(r.data["count"], 1)

    def test_showtime_serializer_has_prices(self):
        r = self.client.get(f"/api/showtimes/{self.showtime.id}/")
        self.assertIn("prices", r.data)
        self.assertIn("regular", r.data["prices"])

    def test_seat_map_state(self):
        r = self.client.get(f"/api/showtimes/{self.showtime.id}/seats/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(len(r.data), self.screen.rows * self.screen.columns)

    def test_cinema_detail_by_slug(self):
        r = self.client.get(f"/api/cinemas/{self.cinema.slug}/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data["name"], self.cinema.name)

    def test_movie_detail_showtimes_include_cinema(self):
        r = self.client.get(f"/api/movies/{self.movie.slug}/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertIn("showtimes_by_date", r.data)
        flat = [st for group in r.data["showtimes_by_date"].values() for st in group]
        self.assertTrue(any(st["cinema"] == self.cinema.name for st in flat))

    def test_movie_detail_showtimes_use_select_related(self):
        # second showtime on a second screen/cinema - must not add queries (N+1 guard)
        cinema2 = make_cinema("Other", city="Delhi")
        screen2 = make_screen(cinema2)
        make_seats(screen2)
        make_showtime(self.movie, screen2, start=time(14, 0))
        with self.assertNumQueries(6):
            r = self.client.get(f"/api/movies/{self.movie.slug}/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_movie_detail_hides_past_showtimes(self):
        from datetime import timedelta

        # today's morning show already started -> hidden
        make_showtime(self.movie, self.screen, show_date=date.today(), start=time(0, 0))
        r = self.client.get(f"/api/movies/{self.movie.slug}/")
        flat = [st for group in r.data["showtimes_by_date"].values() for st in group]
        self.assertEqual(len(flat), 1)  # only tomorrow's 10:00 show
        self.assertEqual(flat[0]["time"], "10:00")
