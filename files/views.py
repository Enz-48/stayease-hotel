"""
Views for StayEase — each function maps to a page in uifinal3.html.

Page 1  → login_view        → GET/POST /
Page 2  → register_view     → GET/POST /register/
Page 3  → home_view         → GET /home/
Page 4  → search_view       → GET /rooms/
Page 5  → booking_view      → GET/POST /book/<room_id>/
         confirm_view       → POST /confirm/
         success_view       → GET /booking/success/<booking_id>/
"""
import hashlib
from decimal import Decimal
from datetime import date

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .models import Guest, Room, RoomType, Service, Reservation, Payment, ReservationService
from .forms import GuestLoginForm, GuestRegisterForm, RoomSearchForm, BookingForm, RatingForm


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _hash_password(raw_password):
    """Simple SHA-256 hash for guest passwords stored in session."""
    return hashlib.sha256(raw_password.encode()).hexdigest()


def _get_logged_in_guest(request):
    """Return the Guest object if logged in, else None."""
    guest_id = request.session.get('guest_id')
    if not guest_id:
        return None
    try:
        return Guest.objects.get(pk=guest_id)
    except Guest.DoesNotExist:
        return None


def _login_required(view_func):
    """Custom decorator — redirects to login if guest is not in session."""
    def wrapper(request, *args, **kwargs):
        if not request.session.get('guest_id'):
            messages.warning(request, 'Please log in to continue.')
            return redirect('hotel:login')
        return view_func(request, *args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return wrapper


ROOM_UPGRADE_PRICES = {
    'Standard': Decimal('0'),
    'Superior': Decimal('1500'),
    'Deluxe': Decimal('3000'),
    'Suite': Decimal('8000'),
}
TAX_RATE = Decimal('0.12')


# ─── PAGE 1: Login ────────────────────────────────────────────────────────────

def login_view(request):
    """Login page — maps to #loginPage in HTML."""
    if request.session.get('guest_id'):
        return redirect('hotel:home')

    form = GuestLoginForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        identifier = form.cleaned_data['username_or_email']
        password = form.cleaned_data['password']
        hashed = _hash_password(password)

        # Look up guest by email (primary identifier)
        try:
            guest = Guest.objects.get(email_address=identifier)
        except Guest.DoesNotExist:
            guest = None

        # Check password hash stored in session store (simple approach)
        stored_hash = request.session.get(f'pwd_{identifier}')

        if guest and stored_hash and stored_hash == hashed:
            request.session['guest_id'] = guest.guest_id
            request.session['guest_name'] = guest.first_name
            messages.success(request, f'Welcome back, {guest.first_name}!')
            return redirect('hotel:home')
        else:
            messages.error(request, 'Invalid username/email or password.')

    return render(request, 'hotel/login.html', {'form': form})


# ─── PAGE 2: Register ─────────────────────────────────────────────────────────

def register_view(request):
    """Register page — maps to #registerPage in HTML."""
    if request.session.get('guest_id'):
        return redirect('hotel:home')

    form = GuestRegisterForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        guest = form.save()
        password = form.cleaned_data['password']
        hashed = _hash_password(password)

        # Store password hash keyed by email so we can verify on login
        request.session[f'pwd_{guest.email_address}'] = hashed

        messages.success(request, 'Account created! Please log in.')
        return redirect('hotel:login')

    return render(request, 'hotel/register.html', {'form': form})


# ─── PAGE 3: Home (Date Search) ───────────────────────────────────────────────

@_login_required
def home_view(request):
    """Home page with search box — maps to #homePage in HTML."""
    guest = _get_logged_in_guest(request)
    form = RoomSearchForm()
    return render(request, 'hotel/home.html', {'guest': guest, 'form': form})


# ─── PAGE 4: Room Availability (Search Results) ───────────────────────────────

@_login_required
def search_view(request):
    """
    Room availability page — maps to #searchPage in HTML.
    Queries available rooms from the DB for the given dates.
    """
    guest = _get_logged_in_guest(request)

    checkin = request.GET.get('checkin') or str(date.today())
    checkout = request.GET.get('checkout') or str(date.today())
    adults = request.GET.get('adults', 2)
    children = request.GET.get('children', 0)

    # Parse dates
    try:
        from datetime import datetime
        checkin_date = datetime.strptime(checkin, '%Y-%m-%d').date()
        checkout_date = datetime.strptime(checkout, '%Y-%m-%d').date()
    except ValueError:
        checkin_date = date.today()
        checkout_date = date.today()

    # Get all rooms with their type
    rooms = Room.objects.select_related('room_type').all()

    # Annotate each room with its status for the requested dates
    room_data = []
    for room in rooms:
        # Find active reservations overlapping the search window
        overlapping = Reservation.objects.filter(
            room=room,
            cancel=False,
            check_in_date__lt=checkout_date,
            check_out_date__gt=checkin_date,
        )
        if overlapping.exists():
            res = overlapping.order_by('-booking_id').first()
            payment = Payment.objects.filter(booking=res).first()
            if payment and payment.status == 'Confirmed':
                status = 'received'
            elif payment and payment.status == 'Pending':
                status = 'pending'
            else:
                status = 'occupied'
        else:
            status = 'vacant'

        room_data.append({
            'room': room,
            'status': status,
            'amenities': room.amenities.split('•') if room.amenities else [],
        })

    # Filter by status checkboxes
    status_filter = request.GET.getlist('status')
    if status_filter:
        room_data = [r for r in room_data if r['status'] in status_filter]

    # Filter by price range
    price_range = request.GET.get('price_range')
    if price_range == 'under_2000':
        room_data = [r for r in room_data if r['room'].room_price < 2000]
    elif price_range == '2000_5000':
        room_data = [r for r in room_data if 2000 <= r['room'].room_price <= 5000]
    elif price_range == '5000_10000':
        room_data = [r for r in room_data if 5000 < r['room'].room_price <= 10000]
    elif price_range == 'over_10000':
        room_data = [r for r in room_data if r['room'].room_price > 10000]

    # Sort
    sort = request.GET.get('sort', 'recommended')
    if sort == 'price_asc':
        room_data.sort(key=lambda r: r['room'].room_price)
    elif sort == 'price_desc':
        room_data.sort(key=lambda r: r['room'].room_price, reverse=True)
    elif sort == 'available_first':
        room_data.sort(key=lambda r: (0 if r['status'] == 'vacant' else 1))

    vacant_count = sum(1 for r in room_data if r['status'] == 'vacant')

    context = {
        'guest': guest,
        'room_data': room_data,
        'vacant_count': vacant_count,
        'checkin': checkin,
        'checkout': checkout,
        'adults': adults,
        'children': children,
        'checkin_date': checkin_date,
        'checkout_date': checkout_date,
    }
    return render(request, 'hotel/search.html', context)


# ─── PAGE 5: Booking Details ──────────────────────────────────────────────────

@_login_required
def booking_view(request, room_id):
    """
    Booking page — maps to #bookingPage in HTML.
    Shows room details and booking form.
    """
    guest = _get_logged_in_guest(request)
    room = get_object_or_404(Room, pk=room_id)

    checkin = request.GET.get('checkin', str(date.today()))
    checkout = request.GET.get('checkout', str(date.today()))

    # Get all services from DB for the selection grid
    services = Service.objects.all()
    service_choices = [(str(s.service_id), f'{s.service_name} — ₱{s.price}') for s in services]

    initial_data = {
        'first_name': guest.first_name,
        'last_name': guest.last_name,
        'email': guest.email_address,
        'checkin': checkin,
        'checkout': checkout,
        'room_id': room_id,
    }

    if request.method == 'POST':
        form = BookingForm(request.POST, service_choices=service_choices)
        if form.is_valid():
            return _process_booking(request, form, room, guest, services)
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form = BookingForm(initial=initial_data, service_choices=service_choices)

    # Calculate nights for display
    try:
        from datetime import datetime
        checkin_date = datetime.strptime(checkin, '%Y-%m-%d').date()
        checkout_date = datetime.strptime(checkout, '%Y-%m-%d').date()
        nights = (checkout_date - checkin_date).days
    except Exception:
        nights = 1

    context = {
        'guest': guest,
        'room': room,
        'form': form,
        'services': services,
        'checkin': checkin,
        'checkout': checkout,
        'nights': nights,
        'tax_rate': int(TAX_RATE * 100),
    }
    return render(request, 'hotel/booking.html', context)


def _process_booking(request, form, room, guest, services):
    """Create Reservation, Payment, and ReservationService records."""
    from datetime import datetime

    data = form.cleaned_data
    checkin_date = data['checkin']
    checkout_date = data['checkout']
    nights = (checkout_date - checkin_date).days

    # Update guest name/email if changed
    guest.first_name = data['first_name']
    guest.last_name = data['last_name']
    guest.save()

    # Calculate total
    upgrade_price = ROOM_UPGRADE_PRICES.get(data['room_type_upgrade'], Decimal('0'))
    selected_service_ids = [int(sid) for sid in data.get('services', [])]
    selected_services = services.filter(service_id__in=selected_service_ids)
    services_total = sum(s.price for s in selected_services)

    base_total = room.room_price * nights
    upgrade_total = upgrade_price * nights
    subtotal = base_total + upgrade_total + services_total
    tax = subtotal * TAX_RATE
    grand_total = subtotal + tax

    # Create Reservation
    reservation = Reservation.objects.create(
        check_in_date=checkin_date,
        check_out_date=checkout_date,
        s_duration=nights,
        cancel=False,
        guest=guest,
        room=room,
    )

    # Link services (RESERVATION_SERVICE)
    for service in selected_services:
        ReservationService.objects.create(booking=reservation, service=service)

    # Create Payment
    Payment.objects.create(
        total_amount=round(grand_total, 2),
        status='Pending',
        payment_method=data['payment_method'],
        booking=reservation,
    )

    request.session['last_booking_id'] = reservation.booking_id
    return redirect('hotel:booking_success', booking_id=reservation.booking_id)


# ─── Booking Success ──────────────────────────────────────────────────────────

@_login_required
def booking_success_view(request, booking_id):
    """Success confirmation page after booking."""
    guest = _get_logged_in_guest(request)
    reservation = get_object_or_404(Reservation, pk=booking_id, guest=guest)
    payment = Payment.objects.filter(booking=reservation).first()

    context = {
        'guest': guest,
        'reservation': reservation,
        'payment': payment,
        'services': reservation.services.all(),
    }
    return render(request, 'hotel/booking_success.html', context)


# ─── Logout ───────────────────────────────────────────────────────────────────

def logout_view(request):
    """Clear session and redirect to login."""
    request.session.flush()
    messages.info(request, 'You have been logged out.')
    return redirect('hotel:login')


# ─── API: Room Availability (JSON for AJAX calls from HTML) ───────────────────

def room_availability_api(request):
    """
    JSON endpoint for the HTML frontend to query room status dynamically.
    GET /api/rooms/?checkin=YYYY-MM-DD&checkout=YYYY-MM-DD
    """
    checkin = request.GET.get('checkin')
    checkout = request.GET.get('checkout')

    if not checkin or not checkout:
        return JsonResponse({'error': 'checkin and checkout required'}, status=400)

    try:
        from datetime import datetime
        checkin_date = datetime.strptime(checkin, '%Y-%m-%d').date()
        checkout_date = datetime.strptime(checkout, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': 'Invalid date format'}, status=400)

    rooms = Room.objects.select_related('room_type').all()
    result = []

    for room in rooms:
        overlapping = Reservation.objects.filter(
            room=room, cancel=False,
            check_in_date__lt=checkout_date,
            check_out_date__gt=checkin_date,
        )
        status = 'vacant'
        if overlapping.exists():
            res = overlapping.order_by('-booking_id').first()
            payment = Payment.objects.filter(booking=res).first()
            if payment and payment.status == 'Confirmed':
                status = 'received'
            elif payment and payment.status == 'Pending':
                status = 'pending'
            else:
                status = 'occupied'

        result.append({
            'room_id': room.room_id,
            'room_type': room.room_type.type_name if room.room_type else '',
            'price': float(room.room_price),
            'amenities': room.amenities or '',
            'status': status,
        })

    return JsonResponse({'rooms': result})
