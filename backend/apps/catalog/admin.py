from django.contrib import admin

from .models import Actor, Event, EventCategory, Genre, Movie, Review


class GenreAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ["name"]


class MovieAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "language", "release_date", "duration", "trending")
    list_filter = ("status", "language", "genres", "trending")
    search_fields = ("title", "director", "description")
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("genres", "cast")
    list_editable = ("status", "trending")


class EventAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "city", "starts_at", "status")
    list_filter = ("category", "status", "city")
    search_fields = ("title", "venue", "city")
    prepopulated_fields = {"slug": ("title",)}


class ReviewAdmin(admin.ModelAdmin):
    list_display = ("movie", "user", "rating", "created_at")
    list_filter = ("rating",)
    search_fields = ("movie__title", "user__username")


admin.site.register(Genre, GenreAdmin)
admin.site.register(Actor)
admin.site.register(Movie, MovieAdmin)
admin.site.register(EventCategory)
admin.site.register(Event, EventAdmin)
admin.site.register(Review, ReviewAdmin)
