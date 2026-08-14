"""Seed the database with demo catalogue, cinemas, showtimes and events.

Usage:
    python manage.py seed_data

Idempotent: safe to run more than once. Also creates a demo user
(username: demo / password: demo12345) and a staff user (admin / admin12345)
unless they already exist.
"""
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

GENRES = ["Action", "Drama", "Comedy", "Thriller", "Sci-Fi", "Romance", "Animation", "Horror", "Biography", "Crime"]

MOVIES = [
    {
        "title": "Punjab '95",
        "desc": "Based on the life of prominent human rights activist Jaswant Singh Khalra.",
        "duration": 169, "language": "Punjabi", "certification": "U/A",
        "director": "Honey Trehan", "status": "now_showing", "trending": True,
        "release_offset": 4, "actors": ["Diljit Dosanjh", "Saurabh Sachdeva", "Veer Abhinav"],
        "genres": ["Drama", "Biography", "Thriller"],
    },
    {
        "title": "Dhurandhar: The Revenge",
        "desc": "Jaskirat Singh Rangi descends deeper into his alias as Hamza Ali Mazari, rising through Karachi's criminal hierarchy to claim the feared title 'Sher-e-Baloch' while balancing loyalty, betrayal, and survival in a ruthless underworld.",
        "duration": 235, "language": "Hindi", "certification": "A",
        "director": "Aditya Dhar", "status": "now_showing", "trending": True,
        "release_offset": 20, "actors": ["Ranveer Singh", "Akshaye Khanna", "Sanjay Dutt"],
        "genres": ["Action", "Crime", "Drama"],
    },
    {
        "title": "Dhamaal 4",
        "desc": "A century-old hidden treasure drives greedy individuals to risk everything, landing them in dangerous situations that test their resolve and relationships.",
        "duration": 143, "language": "Hindi", "certification": "U/A",
        "director": "Indra Kumar", "status": "now_showing", "trending": True,
        "release_offset": 30, "actors": ["Ajay Devgn", "Ravi Kishan", "Sanjeeda Sheikh"],
        "genres": ["Comedy", "Action"],
    },
    {
        "title": "Cocktail 2",
        "desc": "After a decade together, Diya and Kunal's relationship is shaken when Ally, an old friend, re-enters their lives. What begins as a plan between two women spirals into chaos, triggering a hilarious, emotional rollercoaster none of them saw coming.",
        "duration": 150, "language": "Hindi", "certification": "U/A",
        "director": "Homi Adajania", "status": "now_showing", "trending": True,
        "release_offset": 40, "actors": ["Shahid Kapoor", "Kriti Sanon", "Rashmika Mandanna"],
        "genres": ["Romance", "Comedy", "Drama"],
    },
    {
        "title": "Ikkis",
        "desc": "Biographical action drama about the real-life experiences of Second Lieutenant Arun Khetarpal during the India-Pakistan war of 1971.",
        "duration": 144, "language": "Hindi", "certification": "U/A",
        "director": "Sriram Raghavan", "status": "now_showing", "trending": False,
        "release_offset": 50, "actors": ["Dharmendra", "Jaideep Ahlawat", "Agastya Nanda"],
        "genres": ["Action", "Drama", "Biography"],
    },
    {
        "title": "Main Vaapas Aaunga",
        "desc": "A story of love, longing and belonging rooted in Partition-era migration. Examines memory, nostalgia, and emotional ties to home and loved ones, exploring how the past shapes identity and sustains the human spirit across generations.",
        "duration": 167, "language": "Hindi", "certification": "U/A",
        "director": "Imtiaz Ali", "status": "now_showing", "trending": False,
        "release_offset": 60, "actors": ["Diljit Dosanjh", "Naseeruddin Shah", "Vedang Raina"],
        "genres": ["Drama", "Romance"],
    },
    {
        "title": "Border 2",
        "desc": "Young Indian fighters prepared to protect their homeland from a greater threat during the 1971 Indo-Pak war.",
        "duration": 200, "language": "Hindi", "certification": "A",
        "director": "Anurag Singh", "status": "now_showing", "trending": False,
        "release_offset": 70, "actors": ["Sunny Deol", "Varun Dhawan", "Diljit Dosanjh"],
        "genres": ["Action", "Drama"],
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
                obj.genres.set([g for g in genres if g.name in m.get("genres", [])])
                obj.cast.set([actors[n] for n in m["actors"] if n in actors])
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
        start_times = [time(10, 30), time(13, 0), time(15, 30), time(18, 0), time(20, 30), time(23, 0)]
        for day in range(0, 4):
            show_date = today + timedelta(days=day)
            for cinema in cinema_objs:
                for screen in cinema.screens.all():
                    for idx, movie in enumerate(show_movies):
                        start = start_times[idx % len(start_times)]
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
                Review.objects.create(user=demo, movie=movie, rating=5, comment="Great seats and smooth booking experience!")

        self.stdout.write(self.style.SUCCESS("Done. Demo user: demo / demo12345, admin: admin / admin12345"))
