from django.contrib import admin
from django.utils.html import format_html

from .models import Cinema, Screen, Seat, Showtime


class ScreenInline(admin.TabularInline):
    model = Screen
    extra = 0


class CinemaAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "is_active")
    list_filter = ("city", "is_active")
    search_fields = ("name", "city", "address")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ScreenInline]


class SeatAdmin(admin.ModelAdmin):
    list_display = ("screen", "row", "number", "category", "base_price")
    list_filter = ("category", "screen__cinema")
    search_fields = ("screen__name", "row")
    list_editable = ("category", "base_price")


class ShowtimeAdmin(admin.ModelAdmin):
    list_display = ("movie", "screen", "show_date", "start_time", "base_price", "status")
    list_filter = ("show_date", "status", "screen__cinema")
    search_fields = ("movie__title", "screen__name")
    list_editable = ("status", "base_price")


admin.site.register(Cinema, CinemaAdmin)
admin.site.register(Screen)
admin.site.register(Seat, SeatAdmin)
admin.site.register(Showtime, ShowtimeAdmin)
