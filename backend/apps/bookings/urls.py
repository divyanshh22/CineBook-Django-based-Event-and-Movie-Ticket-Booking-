from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    BookingViewSet,
    LockSeatsView,
    PricePreviewView,
    ProcessPaymentView,
    TicketDownloadView,
)

router = DefaultRouter()
router.register("bookings", BookingViewSet)

urlpatterns = [
    path("bookings/lock/", LockSeatsView.as_view(), name="lock-seats"),
    path("bookings/price/", PricePreviewView.as_view(), name="price-preview"),
    path("payments/process/", ProcessPaymentView.as_view(), name="process-payment"),
    path("bookings/<str:code>/ticket/", TicketDownloadView.as_view(), name="ticket-download"),
] + router.urls
