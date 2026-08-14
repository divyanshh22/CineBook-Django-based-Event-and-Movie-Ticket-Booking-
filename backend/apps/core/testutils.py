"""Small factories so tests don't repeat model-creation boilerplate."""
from datetime import date, time, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.utils import timezone

from accounts.models import User
from catalog.models import Genre, Movie, Review
from cinemas.models import Cinema, Screen, Seat, Showtime

User = get_user_model()


def make_user(username="alice", **kwargs):
    return User.objects.create_user(username=username, email=f"{username}@test.local", password="Str0ng!Pass123", **kwargs)


def make_genre(name="Action"):
    return Genre.objects.get_or_create(name=name)[0]


def make_movie(title="Test Flick", status=Movie.Status.NOW_SHOWING, release_date=None, rating_genre=None, **kwargs):
    defaults = {
        "duration": 120,
        "release_date": release_date or (date.today() - timedelta(days=3)),
        "language": "English",
        "certification": "U/A",
        "director": "Someone",
        "status": status,
    }
    defaults.update(kwargs)
    movie = Movie.objects.create(title=title, **defaults)
    if rating_genre:
        movie.genres.add(rating_genre)
    return movie


def make_cinema(name="Galaxy Cineplex", city="Mumbai"):
    return Cinema.objects.create(name=name, city=city, address="1 Test Street", amenities="Parking")


def make_screen(cinema, name="Screen 1", rows=6, columns=8, screen_type=Screen.ScreenType.STANDARD):
    return Screen.objects.create(cinema=cinema, name=name, rows=rows, columns=columns, screen_type=screen_type)


def make_seats(screen, base_price=Decimal("200")):
    seats = []
    for r in range(screen.rows):
        for n in range(1, screen.columns + 1):
            seats.append(
                Seat.objects.create(
                    screen=screen,
                    row=chr(ord("A") + r),
                    number=n,
                    category=Seat.Category.REGULAR if r < screen.rows - 2 else Seat.Category.PREMIUM,
                    base_price=base_price,
                )
            )
    return seats


def make_showtime(movie, screen, show_date=None, start=time(10, 0), base_price=Decimal("200")):
    return Showtime.objects.create(
        screen=screen,
        movie=movie,
        show_date=show_date or date.today() + timedelta(days=1),
        start_time=start,
        end_time=time(12, 0),
        base_price=base_price,
    )


def give_review(user, movie, rating=4, comment="Good"):
    return Review.objects.create(user=user, movie=movie, rating=rating, comment=comment)
