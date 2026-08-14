"""Seed the database with demo catalogue, cinemas, showtimes and events.

Usage:
    python manage.py seed_data

Idempotent: safe to run more than once. Also creates a demo user
(username: demo / password: demo12345) and a staff user (admin / admin12345)
unless they already exist.
"""
import random
from datetime import date, time, timedelta
from decimal import Decimal
from io import BytesIO

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from PIL import Image, ImageDraw, ImageFont

from accounts.models import User
from catalog.models import Actor, Event, EventCategory, Genre, Movie, Review
from cinemas.models import Cinema, Screen, Seat, Showtime

GENRES = ["Action", "Drama", "Comedy", "Thriller", "Sci-Fi", "Romance", "Animation", "Horror"]

MOVIES = [
    {
        "title": "Neon Horizon",
        "desc": "A rogue engineer discovers a city-sized simulation hiding the truth about humanity. A visual feast that never lets go.",
        "duration": 148, "language": "English", "certification": "U/A",
        "director": "Arjun Mehta", "status": "now_showing", "trending": True,
        "release_offset": 5, "actors": ["Aditya Rao", "Meera Kapoor", "Daniel Cruz"],
    },
    {
        "title": "Midnight Trains",
        "desc": "Three strangers share a sleeper berth and a secret that could topple a corporation by sunrise.",
        "duration": 121, "language": "Hindi", "certification": "U/A",
        "director": "Sara Fernandes", "status": "now_showing", "trending": True,
        "release_offset": 12, "actors": ["Rohan Desai", "Zoya Sheikh"],
    },
    {
        "title": "Paper Planes",
        "desc": "A warm, funny story about a retired teacher and the street kids who teach him to fly again.",
        "duration": 112, "language": "Hindi", "certification": "U",
        "director": "Vikram Nair", "status": "now_showing", "trending": False,
        "release_offset": 20, "actors": ["Ishaan Kulkarni"],
    },
    {
        "title": "Static Bloom",
        "desc": "A botanist on a ruined space station keeps the last flower on Earth alive while the AI above decides its fate.",
        "duration": 134, "language": "English", "certification": "U/A",
        "director": "Nadia Rahman", "status": "now_showing", "trending": False,
        "release_offset": 26, "actors": ["Meera Kapoor", "Jon Bell"],
    },
    {
        "title": "Crimson Quarry",
        "desc": "An archaeologist and a small-town cop uncover a smuggling ring beneath a 400-year-old mine.",
        "duration": 140, "language": "English", "certification": "A",
        "director": "Marco Alvarez", "status": "now_showing", "trending": False,
        "release_offset": 34, "actors": ["Daniel Cruz", "Zoya Sheikh"],
    },
    {
        "title": "Biryani Diaries",
        "desc": "A chaotic family cooks one enormous pot of biryani at a wedding while old grievances bubble to the surface.",
        "duration": 105, "language": "Hindi", "certification": "U",
        "director": "Farhan Qureshi", "status": "now_showing", "trending": False,
        "release_offset": 41, "actors": ["Rohan Desai", "Ishaan Kulkarni"],
    },
    {
        "title": "The Last Lighthouse",
        "desc": "A lonely keeper and a mysterious visitor trade stories through one storm-filled night.",
        "duration": 96, "language": "English", "certification": "U",
        "director": "Elena Fischer", "status": "upcoming", "trending": False,
        "release_offset": 21, "actors": ["Jon Bell"],
    },
    {
        "title": "Monsoon Circuit",
        "desc": "Two rival auto mechanics accidentally enter a cross-country race during the monsoon.",
        "duration": 118, "language": "Hindi", "certification": "U/A",
        "director": "Aditya Rao", "status": "upcoming", "trending": True,
        "release_offset": 28, "actors": ["Zoya Sheikh", "Rohan Desai"],
    },
    {
        "title": "Echo Chamber",
        "desc": "A podcaster realises every guest she interviews has already heard her episodes before meeting her.",
        "duration": 109, "language": "English", "certification": "U/A",
        "director": "Tom Iverson", "status": "upcoming", "trending": False,
        "release_offset": 35, "actors": ["Meera Kapoor", "Daniel Cruz"],
    },
    {
        "title": "Rocket Rickshaw",
        "desc": "A madcap animated adventure about a rickshaw that accidentally flies to the moon.",
        "duration": 94, "language": "Hindi", "certification": "U",
        "director": "Ananya Bose", "status": "upcoming", "trending": False,
        "release_offset": 42, "actors": [],
    },
]

CINEMAS = [
    {
        "name": "Starlight Cinemas",
        "city": "Delhi", "state": "DL",
        "address": "Connaught Place, New Delhi",
        "amenities": "Parking, Food Court, IMAX",
        "screens": [
            ("Screen 1", "standard", 8, 12),
            ("Screen 2", "platinum", 6, 10),
            ("Screen 3", "screenx", 9, 12),
        ],
    },
    {
        "name": "Regal Gold",
        "city": "Bengaluru", "state": "KA",
        "address": "MG Road, Bengaluru",
        "amenities": "Food Court, Recliners, VIP Lounge",
        "screens": [
            ("Screen 1", "vip", 6, 9),
            ("Screen 2", "standard", 9, 12),
        ],
    },
    {
        "name": "Bhopal Cinehall",
        "city": "Bhopal", "state": "MP",
        "address": "New Market, Bhopal",
        "amenities": "Parking, Food Court, Dolby Atmos",
        "screens": [
            ("Screen 1", "imax", 10, 14),
            ("Screen 2", "standard", 8, 12),
        ],
    },
]

EVENT_CATEGORIES = ["Music", "Comedy", "Theatre", "Sports", "Workshop"]

EVENTS = [
    {
        "title": "Monsoon Indie Music Night",
        "cat": "Music", "venue": "Juhu Amphitheatre", "city": "Mumbai",
        "start_offset": 9, "duration_h": 3, "price": 899,
        "desc": "Five indie bands, one open-air amphitheatre, and a sky about to pour. Bring your raincoat.",
    },
    {
        "title": "Late Night Laughs: Stand-up",
        "cat": "Comedy", "venue": "The Comedy Cellar", "city": "Delhi",
        "start_offset": 15, "duration_h": 2, "price": 499,
        "desc": "Four of the city's funniest comics, one stage, zero filters.",
    },
    {
        "title": "The Glass Menagerie",
        "cat": "Theatre", "venue": "Prithvi Theatre", "city": "Mumbai",
        "start_offset": 22, "duration_h": 2, "price": 749,
        "desc": "A moving revival of Tennessee Williams' classic family drama.",
    },
    {
        "title": "Street Food Walk",
        "cat": "Workshop", "venue": "Old City Market", "city": "Bengaluru",
        "start_offset": 30, "duration_h": 3, "price": 349,
        "desc": "Taste, learn and walk through the lanes that define the city's food.",
    },
]


def make_poster(title, size=(400, 560), colors=None, tag=""):
    """Generate a placeholder poster so the site has real images to show."""
    if colors is None:
        colors = [(124, 92, 255), (34, 211, 238)]
    w, h = size
    img = Image.new("RGB", (w, h))
    draw = ImageDraw.Draw(img)
    for y in range(h):
        t = y / h
        r = int(colors[0][0] + (colors[1][0] - colors[0][0]) * t)
        g = int(colors[0][1] + (colors[1][1] - colors[0][1]) * t)
        b = int(colors[0][2] + (colors[1][2] - colors[0][2]) * t)
        draw.line([(0, y), (w, y)], fill=(r, g, b))

    try:
        font = ImageFont.truetype("arial.ttf", 34)
        small = ImageFont.truetype("arial.ttf", 18)
    except OSError:
        font = ImageFont.load_default()
        small = font

    lines = []
    for word in title.split():
        if lines and len(lines[-1]) + len(word) < 16:
            lines[-1] += " " + word
        else:
            lines.append(word)

    y = h - 150
    for line in lines[:4]:
        draw.text((28, y), line, fill=(255, 255, 255), font=font)
        y += 42
    draw.text((28, h - 48), tag, fill=(255, 255, 255), font=small)
    draw.rectangle([(0, h - 8), (w, h)], fill=(0, 0, 0))

    buf = BytesIO()
    img.save(buf, format="PNG")
    return ContentFile(buf.getvalue(), name=f"{title.lower().replace(' ', '-')}.png")


def set_image_field(instance, field, content):
    setattr(instance, field, content)
    instance.save()


class Command(BaseCommand):
    help = "Seed demo data for CineBook."

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Seeding genres...")
        genres = [Genre.objects.get_or_create(name=n)[0] for n in GENRES]

        self.stdout.write("Seeding actors...")
        actors = {}
        for movie in MOVIES:
            for name in movie["actors"]:
                actor, _ = Actor.objects.get_or_create(name=name)
                actors[name] = actor

        self.stdout.write("Seeding movies...")
        rng = random.Random(42)
        today = date.today()
        movie_objs = []
        for i, m in enumerate(MOVIES):
            obj, created = Movie.objects.get_or_create(
                title=m["title"],
                defaults={
                    "description": m["desc"],
                    "duration": m["duration"],
                    "language": m["language"],
                    "certification": m["certification"],
                    "director": m["director"],
                    "status": m["status"],
                    "trending": m["trending"],
                    "release_date": today - timedelta(days=m["release_offset"]),
                },
            )
            if created:
                set_image_field(obj, "poster", make_poster(m["title"], tag=f"{m['language']} | {m['certification']}"))
                obj.genres.set(rng.sample(genres, k=3))
                obj.cast.set([actors[n] for n in m["actors"] if n in actors])
                for _ in range(rng.randint(2, 5)):
                    pass  # reviews seeded separately below
            movie_objs.append(obj)
            self.stdout.write(f"  - {m['title']}")

        self.stdout.write("Seeding cinemas/screens/seats...")
        cinema_objs = []
        for c in CINEMAS:
            cinema, created = Cinema.objects.get_or_create(
                name=c["name"],
                defaults={
                    "city": c["city"], "state": c["state"],
                    "address": c["address"], "amenities": c["amenities"],
                },
            )
            if created:
                set_image_field(cinema, "image", make_poster(cinema.name, size=(800, 450), tag="CineBook", colors=[(30, 41, 82), (88, 28, 135)]))
            cinema_objs.append(cinema)

            for sname, stype, rows, cols in c["screens"]:
                screen, _ = Screen.objects.get_or_create(
                    cinema=cinema, name=sname,
                    defaults={"screen_type": stype, "rows": rows, "columns": cols},
                )
                if not screen.seats.exists():
                    base = {"standard": 200, "imax": 320, "dolby": 260, "platinum": 450, "screenx": 280, "vip": 500}[stype]
                    seats = []
                    for r in range(rows):
                        label = chr(ord("A") + r)
                        for n in range(1, cols + 1):
                            if r >= rows - 1:
                                cat, mult = Seat.Category.VIP, Decimal("1.8")
                            elif r >= rows - 3:
                                cat, mult = Seat.Category.PREMIUM, Decimal("1.4")
                            else:
                                cat, mult = Seat.Category.REGULAR, Decimal("1.0")
                            seats.append(Seat(
                                screen=screen, row=label, number=n, category=cat,
                                base_price=(base * mult).quantize(Decimal("0.01")),
                            ))
                    Seat.objects.bulk_create(seats)

        self.stdout.write("Seeding showtimes...")
        show_movies = [m for m in movie_objs if m.status == Movie.Status.NOW_SHOWING]
        for day in range(0, 4):
            show_date = today + timedelta(days=day)
            for cinema in cinema_objs:
                for screen in cinema.screens.all():
                    for idx, movie in enumerate(show_movies[:2]):
                        start = time(11 + idx * 5, 30) if day % 2 == 0 else time(10 + idx * 6, 0)
                        end = (timezone.datetime.combine(show_date, start) + timedelta(minutes=movie.duration)).time()
                        Showtime.objects.get_or_create(
                            screen=screen, show_date=show_date, start_time=start,
                            defaults={
                                "movie": movie, "end_time": end,
                                "base_price": screen.seats.filter(category=Seat.Category.REGULAR).first().base_price
                                if screen.seats.exists() else 200,
                            },
                        )

        self.stdout.write("Seeding events...")
        for e in EVENTS:
            cat = EventCategory.objects.get_or_create(name=e["cat"])[0]
            start = timezone.now() + timedelta(days=e["start_offset"])
            Event.objects.get_or_create(
                title=e["title"],
                defaults={
                    "description": e["desc"],
                    "category": cat, "venue": e["venue"], "city": e["city"],
                    "starts_at": start.replace(minute=0, second=0, microsecond=0),
                    "ends_at": start + timedelta(hours=e["duration_h"]),
                    "ticket_price": e["price"],
                },
            )

        self.stdout.write("Seeding users + reviews...")
        demo, _ = User.objects.get_or_create(
            username="demo",
            defaults={"email": "demo@cinebook.local", "first_name": "Demo"},
        )
        if not demo.has_usable_password():
            demo.set_password("demo12345")
            demo.save()
        admin_user, _ = User.objects.get_or_create(
            username="admin",
            defaults={"email": "admin@cinebook.local", "first_name": "Admin", "is_staff": True, "is_superuser": True},
        )
        if not admin_user.has_usable_password():
            admin_user.set_password("admin12345")
            admin_user.save()

        for movie in movie_objs:
            if not Review.objects.filter(movie=movie).exists():
                Review.objects.create(user=demo, movie=movie, rating=rng.randint(3, 5), comment="Great seats and smooth booking experience!")

        self.stdout.write(self.style.SUCCESS("Done. Demo user: demo / demo12345, admin: admin / admin12345"))
