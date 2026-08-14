from django.contrib import admin

from .models import Booking, BookingSeat, Payment, SeatLock


class BookingSeatInline(admin.TabularInline):
    model = BookingSeat
    extra = 0
    readonly_fields = ("seat", "price")


class PaymentInline(admin.StackedInline):
    model = Payment
    extra = 0
    readonly_fields = ("amount", "status", "method", "gateway_transaction_id", "paid_at")


class BookingAdmin(admin.ModelAdmin):
    list_display = ("booking_code", "user", "showtime", "total", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("booking_code", "user__username", "user__email")
    readonly_fields = ("booking_code", "subtotal", "convenience_fee", "tax", "total")
    inlines = [BookingSeatInline, PaymentInline]


class SeatLockAdmin(admin.ModelAdmin):
    list_display = ("token", "user", "showtime", "status", "expires_at")
    list_filter = ("status",)
    search_fields = ("token", "user__username")


class PaymentAdmin(admin.ModelAdmin):
    list_display = ("booking", "amount", "status", "method", "paid_at")
    list_filter = ("status", "method")


admin.site.register(Booking, BookingAdmin)
admin.site.register(SeatLock, SeatLockAdmin)
admin.site.register(Payment, PaymentAdmin)
