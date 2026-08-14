import io

from django.db.models import Q
from django.http import HttpResponse
from django.utils import timezone
from PIL import Image, ImageDraw, ImageFont
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Booking
from .serializers import BookingSerializer, LockSeatsSerializer
from .services import (
    LockError,
    PaymentError,
    cancel_booking,
    lock_seats,
    price_breakdown,
    process_payment,
)


class LockSeatsView(APIView):
    """POST /api/bookings/lock/  - temporarily hold seats for checkout."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = LockSeatsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            lock, error = lock_seats(
                request.user,
                serializer.validated_data["showtime"],
                serializer.validated_data["seat_ids"],
            )
        except LockError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)
        if error:
            return Response({"detail": error}, status=status.HTTP_409_CONFLICT)

        breakdown = price_breakdown(lock.showtime, list(lock.seats.all()))
        return Response(
            {
                "token": lock.token,
                "expires_at": lock.expires_at,
                "seats": [s.label for s in lock.seats.all()],
                "price": breakdown,
            },
            status=status.HTTP_200_OK,
        )


class PricePreviewView(APIView):
    """POST /api/bookings/price/ - compute the cost before locking."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = LockSeatsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        from cinemas.models import Showtime

        try:
            showtime = Showtime.objects.get(pk=serializer.validated_data["showtime"])
        except Showtime.DoesNotExist:
            return Response({"detail": "Showtime not found."}, status=status.HTTP_404_NOT_FOUND)

        seats = list(showtime.screen.seats.filter(id__in=serializer.validated_data["seat_ids"]))
        if len(seats) != len(set(serializer.validated_data["seat_ids"])):
            return Response({"detail": "Invalid seats."}, status=status.HTTP_400_BAD_REQUEST)
        breakdown = price_breakdown(showtime, seats)
        return Response(
            {
                "seats": [s.label for s in seats],
                "price": breakdown,
            }
        )


class BookingViewSet(viewsets.ReadOnlyModelViewSet):
    """The current user's bookings. Query param ``filter=upcoming|past``."""

    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "booking_code"
    queryset = Booking.objects.none()

    def get_queryset(self):
        qs = Booking.objects.filter(user=self.request.user).prefetch_related(
            "seats__seat", "payment"
        ).select_related("showtime__movie", "showtime__screen__cinema")
        mode = self.request.query_params.get("filter")
        today = timezone.localdate()
        if mode == "upcoming":
            qs = qs.filter(showtime__show_date__gte=today, status=Booking.Status.CONFIRMED)
        elif mode == "past":
            qs = qs.filter(
                Q(showtime__show_date__lt=today) | Q(status=Booking.Status.CANCELLED)
            )
        return qs

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["request"] = self.request
        return ctx

    @action(detail=True, methods=["post"])
    def cancel(self, request, booking_code=None):
        booking = self.get_object()
        try:
            cancel_booking(request.user, booking.booking_code)
        except PaymentError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"detail": "Booking cancelled."})


class ProcessPaymentView(APIView):
    """POST /api/payments/process/ - run the (mock) payment for a lock."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        token = request.data.get("lock_token")
        if not token:
            return Response({"detail": "lock_token is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            result = process_payment(request.user, token, request.data.get("method"))
        except PaymentError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)

        booking = result["booking"]
        if result["success"]:
            serializer = BookingSerializer(booking, context={"request": request})
            return Response(
                {"detail": "Payment successful!", "booking": serializer.data},
                status=status.HTTP_201_CREATED,
            )
        return Response(
            {"detail": "Payment failed. Your seats were released."},
            status=status.HTTP_402_PAYMENT_REQUIRED,
        )


def _font(size):
    for name in ("arial.ttf", "DejaVuSans.ttf", "segoeui.ttf", "calibri.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def build_ticket_image(booking):
    """Render the printable ticket (PNG) with a QR code."""
    import qrcode

    payload = {
        "booking_code": booking.booking_code,
        "movie": booking.showtime.movie.title,
        "cinema": booking.showtime.screen.cinema.name,
        "screen": booking.showtime.screen.name,
        "date": str(booking.showtime.show_date),
        "time": str(booking.showtime.start_time),
        "seats": [bs.seat.label for bs in booking.seats.all()],
    }
    qr = qrcode.QRCode(border=1, box_size=5)
    qr.add_data(payload)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")

    W, H = 900, 420
    img = Image.new("RGB", (W, H), "#0a0c13")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, H], fill="#151829")

    accent = (124, 92, 255)
    d.rectangle([0, 0, 14, H], fill=accent)
    d.rectangle([0, 0, W, 6], fill=(34, 211, 238))

    bold = _font(34)
    title = _font(26)
    body = _font(20)
    small = _font(16)
    muted = (154, 161, 188)

    d.text((60, 40), "CineBook", font=bold, fill=(238, 240, 247))
    d.text((60, 92), payload["movie"], font=title, fill=(238, 240, 247))
    d.text((60, 132), f"{payload['cinema']}  |  Screen: {payload['screen']}", font=body, fill=muted)
    d.text((60, 168), f"{payload['date']}  |  {payload['time']}", font=body, fill=muted)
    d.text((60, 206), "SEATS: " + ", ".join(payload["seats"]), font=title, fill=(34, 211, 238))
    d.text((60, 260), f"Booking ID: {booking.booking_code}", font=small, fill=muted)
    d.text((60, 292), f"Total paid: Rs. {booking.total}", font=body, fill=(34, 197, 94))

    img.paste(qr_img, (W - 220, 140, W - 220 + qr_img.width, 140 + qr_img.height))

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


class TicketDownloadView(APIView):
    """GET /api/bookings/<code>/ticket/ - PNG ticket with QR code."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, code):
        try:
            booking = Booking.objects.select_related(
                "showtime__movie", "showtime__screen__cinema", "payment"
            ).prefetch_related("seats__seat").get(
                booking_code=code, user=request.user, status=Booking.Status.CONFIRMED
            )
        except Booking.DoesNotExist:
            return Response({"detail": "Ticket not found."}, status=status.HTTP_404_NOT_FOUND)
        png = build_ticket_image(booking)
        response = HttpResponse(png, content_type="image/png")
        response["Content-Disposition"] = f'attachment; filename="ticket-{booking.booking_code}.png"'
        return response
