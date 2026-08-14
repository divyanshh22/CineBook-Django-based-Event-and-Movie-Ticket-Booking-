from rest_framework import serializers

from .models import Actor, Event, EventCategory, Genre, Movie, Review


class GenreSerializer(serializers.ModelSerializer):
    movie_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Genre
        fields = ["id", "name", "slug", "movie_count"]


class ActorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Actor
        fields = ["id", "name", "photo", "bio"]


class MovieListSerializer(serializers.ModelSerializer):
    genres = serializers.SlugRelatedField(slug_field="name", many=True, read_only=True)
    rating = serializers.SerializerMethodField()
    review_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Movie
        fields = [
            "id", "title", "slug", "poster", "backdrop", "duration",
            "release_date", "language", "certification", "director",
            "status", "trending", "genres", "rating", "review_count",
        ]

    def get_rating(self, obj):
        return obj.average_rating()["average"]


class MovieDetailSerializer(MovieListSerializer):
    cast = ActorSerializer(many=True, read_only=True)
    genres = GenreSerializer(many=True, read_only=True)
    avg_rating = serializers.SerializerMethodField()

    class Meta(MovieListSerializer.Meta):
        fields = MovieListSerializer.Meta.fields + ["description", "trailer_url", "cast", "avg_rating"]

    def get_avg_rating(self, obj):
        agg = obj.average_rating()
        return {"average": agg["average"], "count": agg["count"]}


class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    movie = serializers.PrimaryKeyRelatedField(queryset=Movie.objects.all())

    class Meta:
        model = Review
        fields = ["id", "movie", "user", "rating", "comment", "created_at"]
        read_only_fields = ["user"]

    def validate_rating(self, value):
        if not (1 <= value <= 5):
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value

    def create(self, validated_data):
        user = validated_data.pop("user") or self.context["request"].user
        movie = validated_data["movie"]
        if Review.objects.filter(user=user, movie=movie).exists():
            raise serializers.ValidationError("You have already reviewed this movie.")
        return Review.objects.create(user=user, **validated_data)


class EventCategorySerializer(serializers.ModelSerializer):
    event_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = EventCategory
        fields = ["id", "name", "slug", "event_count"]


class EventSerializer(serializers.ModelSerializer):
    category = serializers.StringRelatedField()

    class Meta:
        model = Event
        fields = [
            "id", "title", "slug", "description", "poster", "category",
            "venue", "city", "starts_at", "ends_at", "ticket_price", "status",
        ]
