from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.core.mail import send_mail, EmailMultiAlternatives
from django.contrib import messages
from django.conf import settings
from django.template.loader import render_to_string
from .models import Register, Room, Reservation, Rating, Payment
import random
from datetime import date, datetime, timedelta


# ==================== ROOM AVAILABILITY HELPERS ====================
def parse_booking_date(value, fallback=None):
    """Safely convert form date values to date objects."""
    if isinstance(value, date):
        return value
    if not value:
        return fallback or date.today()
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return fallback or date.today()


def has_room_date_conflict(room, check_in, check_out, exclude_booking_id=None):
    """
    Returns True when the selected room already has an active reservation
    that overlaps the requested date range.
    Overlap formula: existing_check_in < new_check_out AND existing_check_out > new_check_in.
    """
    active_statuses = ["Pending", "Confirmed", "Received", "Paid", "pending", "confirmed", "received", "paid"]
    conflicts = Reservation.objects.filter(
        room=room,
        status__in=active_statuses,
        check_in__lt=check_out,
        check_out__gt=check_in,
    )
    if exclude_booking_id:
        conflicts = conflicts.exclude(booking_id=exclude_booking_id)
    return conflicts.exists()


def room_is_blocked(room):
    """Permanent/manual room blocking for maintenance or admin-set occupied rooms."""
    return str(getattr(room, "room_status", "vacant") or "vacant").lower() in ["occupied", "maintenance", "unavailable"]



def room_availability_status(request):
    """AJAX endpoint used by finalhtml.html to refresh room availability without reloading the page."""
    check_in = parse_booking_date(request.GET.get('check_in'))
    check_out = parse_booking_date(request.GET.get('check_out'), fallback=check_in + timedelta(days=1))

    active_statuses = ["Pending", "Confirmed", "Received", "Paid", "pending", "confirmed", "received", "paid"]

    reservations = Reservation.objects.filter(
        status__in=active_statuses,
        check_in__lt=check_out,
        check_out__gt=check_in,
    ).select_related('room')

    blocked_rooms = Room.objects.filter(
        room_status__in=["occupied", "maintenance", "unavailable", "Occupied", "Maintenance", "Unavailable"]
    )

    return JsonResponse({
        "reservations": [
            {
                "roomNumber": str(reservation.room.room_number),
                "checkin": reservation.check_in.strftime("%Y-%m-%d"),
                "checkout": reservation.check_out.strftime("%Y-%m-%d"),
                "status": reservation.status,
            }
            for reservation in reservations
        ],
        "blockedRooms": [str(room.room_number) for room in blocked_rooms],
    })

def home(request):
    message = ""
    message_type = ""

    if request.method == 'POST':
        form_type = request.POST.get('form_type')

        if form_type == 'register':
            request.session['login_attempts'] = 0
            request.session.pop('lock_until', None)

            email = request.POST.get('email')
            username = request.POST.get('username')

            if Register.objects.filter(username=username).exists():
                message = "Username already exists. Please choose another username."
                message_type = "error"

            elif Register.objects.filter(email=email).exists():
                message = "Email is already registered. Please log in instead."
                message_type = "error"

            else:
                otp = random.randint(100000, 999999)

                request.session['pending_register'] = {
                    'firstname': request.POST.get('firstname'),
                    'lastname': request.POST.get('lastname'),
                    'email': email,
                    'contact': request.POST.get('contact'),
                    'address': request.POST.get('address'),
                    'username': username,
                    'password': request.POST.get('password'),
                }

                request.session['otp'] = str(otp)

                try:
                    send_mail(
                        'StayEase OTP Verification',
                        f'Your StayEase OTP code is: {otp}',
                        settings.DEFAULT_FROM_EMAIL,
                        [email],
                        fail_silently=False,
                    )
                    print("OTP EMAIL SENT")
                except Exception as e:
                    print("OTP EMAIL FAILED:", e)

                return redirect('hotel:verify_otp')

        elif form_type == 'login':
            attempts = request.session.get('login_attempts', 0)
            lock_until = request.session.get('lock_until')

            if lock_until:
                lock_time = datetime.fromisoformat(lock_until)

                if datetime.now() < lock_time:
                    remaining = int((lock_time - datetime.now()).total_seconds())
                    minutes = remaining // 60
                    seconds = remaining % 60

                    message = f"Too many login attempts. Try again in {minutes}m {seconds}s."
                    message_type = "error"

                    return render(request, 'finalhtml.html', {
                        'message': message,
                        'message_type': message_type,
                        'rooms': Room.objects.all(),
                        'latest_booking_id': (Reservation.objects.order_by('-booking_id').first().booking_id if Reservation.objects.order_by('-booking_id').first() else 0),
                    })
                else:
                    request.session['login_attempts'] = 0
                    request.session.pop('lock_until', None)
                    attempts = 0

            username_or_email = request.POST.get('login_username')
            password = request.POST.get('login_password')

            try:
                user = Register.objects.get(username=username_or_email)
            except Register.DoesNotExist:
                try:
                    user = Register.objects.get(email=username_or_email)
                except Register.DoesNotExist:
                    user = None

            if user is None:
                attempts += 1
                request.session['login_attempts'] = attempts

                if attempts >= 3:
                    lock_time = datetime.now() + timedelta(minutes=1)
                    request.session['lock_until'] = lock_time.isoformat()
                    message = "Maximum login attempts reached. Wait 1 minute."
                else:
                    message = f"Wrong username/email. Attempts left: {3 - attempts}"

                message_type = "error"

            elif user.password == password:
                request.session['login_attempts'] = 0
                request.session.pop('lock_until', None)
                request.session['user_id'] = user.id
                return redirect('/#homePage')

            else:
                attempts += 1
                request.session['login_attempts'] = attempts

                if attempts >= 3:
                    lock_time = datetime.now() + timedelta(minutes=1)
                    request.session['lock_until'] = lock_time.isoformat()
                    message = "Maximum login attempts reached. Wait 1 minute."
                else:
                    message = f"Wrong password. Attempts left: {3 - attempts}"

                message_type = "error"

    rooms = Room.objects.all()

    return render(request, 'finalhtml.html', {
        'message': message,
        'message_type': message_type,
        'rooms': rooms,
        'latest_booking_id': (Reservation.objects.order_by('-booking_id').first().booking_id if Reservation.objects.order_by('-booking_id').first() else 0),
    })


def verify_otp(request):
    if request.method == 'POST':
        user_otp = request.POST.get('otp')
        saved_otp = request.session.get('otp')
        pending = request.session.get('pending_register')

        if not pending:
            messages.error(request, "No pending registration found. Please register again.")
            return redirect('home')

        if user_otp == saved_otp:
            Register.objects.create(
                firstname=pending.get('firstname'),
                lastname=pending.get('lastname'),
                email=pending.get('email'),
                contact=pending.get('contact'),
                address=pending.get('address'),
                username=pending.get('username'),
                password=pending.get('password'),
            )

            request.session.pop('otp', None)
            request.session.pop('pending_register', None)

            messages.success(request, "Account created successfully. You can now log in.")
            return redirect('/#loginPage')

        messages.error(request, "Invalid OTP. Please try again.")

    return render(request, 'verify_otp.html')


def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')

        user = Register.objects.filter(email=email).first()

        if not user:
            messages.error(request, "Email not found.")
            return redirect('/forgot-password/')

        otp = random.randint(100000, 999999)

        request.session['reset_email'] = email
        request.session['reset_otp'] = str(otp)

        try:
            send_mail(
                'StayEase Password Reset OTP',
                f'Your OTP for password reset is: {otp}',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )

            print("RESET OTP SENT")
            messages.success(request, "OTP sent successfully.")
            return redirect('/verify-reset-otp/')

        except Exception as e:
            print("RESET OTP FAILED:", e)
            messages.error(request, "Failed to send OTP.")
            return redirect('/forgot-password/')

    return render(request, 'forgot_password.html')


def verify_reset_otp(request):
    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        saved_otp = request.session.get('reset_otp')

        if entered_otp == saved_otp:
            messages.success(request, "OTP verified successfully.")
            return redirect('/reset-password/')

        messages.error(request, "Invalid OTP.")

    return render(request, 'verify_reset_otp.html')


def reset_password(request):
    email = request.session.get('reset_email')

    if not email:
        messages.error(request, "Session expired.")
        return redirect('/forgot-password/')

    if request.method == 'POST':
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect('/reset-password/')

        user = Register.objects.filter(email=email).first()

        if user:
            user.password = password
            user.save()

            request.session.pop('reset_email', None)
            request.session.pop('reset_otp', None)

            messages.success(request, "Password reset successful.")
            return redirect('/#loginPage')

    return render(request, 'reset_password.html')


def booking(request, room_id):
    room = Room.objects.filter(room_number=str(room_id)).first()

    if not room:
        room = Room.objects.filter(pk=room_id).first()

    if not room:
        messages.error(request, "Selected room does not exist.")
        return redirect('/#homePage')

    room_type = room.room_type

    if request.method == 'POST':
        print("BOOKING FORM DATA:", request.POST)

        guest_email = request.POST.get('email')
        guest_name = request.POST.get('fullname') or request.POST.get('name') or "Guest"
        services = request.POST.get('services') or "No additional services selected"

        check_in = parse_booking_date(
            request.POST.get('check_in')
            or request.POST.get('checkin')
            or request.POST.get('checkIn')
        )

        check_out = parse_booking_date(
            request.POST.get('check_out')
            or request.POST.get('checkout')
            or request.POST.get('checkOut'),
            fallback=check_in + timedelta(days=1)
        )

        if check_out <= check_in:
            messages.error(request, "Invalid booking dates. Check-out must be after check-in.")
            return redirect('/#homePage')

        # Combined availability protection:
        # 1) respect permanent/manual room status, and
        # 2) prevent same-room date overlap from active reservations.
        if room_is_blocked(room):
            messages.error(request, "This room is currently occupied or unavailable.")
            return redirect('/#homePage')

        if has_room_date_conflict(room, check_in, check_out):
            messages.error(request, "This room is already occupied for the selected date.")
            return redirect('/#homePage')

        adults = request.POST.get('adults') or 1
        children = request.POST.get('children') or 0

        guest = Register.objects.filter(email=guest_email).first()

        if not guest:
            guest = Register.objects.create(
                firstname=guest_name,
                lastname="",
                email=guest_email or "noemail@example.com",
                contact=request.POST.get('contact') or "",
                address=request.POST.get('address') or "",
                username=guest_email or f"guest{random.randint(1000, 9999)}",
                password="guest123"
            )

        reservation = Reservation.objects.create(
            guest=guest,
            room=room,
            check_in=check_in,
            check_out=check_out,
            adults=adults,
            children=children,
            status="Pending"
        )

        # NOTE: Do not permanently reduce RoomType.available_rooms or set the room_status
        # to pending here. Availability is date-based, while room_status is reserved for
        # manual/general blocking such as occupied, maintenance, or unavailable.

        total_price = request.POST.get('total_price') or room.price
        payment_method = request.POST.get('payment_method') or "Not specified"

        total_price = str(total_price).replace("₱", "").replace(",", "").strip()

        Payment.objects.create(
            reservation=reservation,
            payment_method=payment_method,
            amount_paid=total_price,
            payment_status="Paid"
        )

        print("PAYMENT SAVED")

        if guest_email:
            try:
                html_content = render_to_string('stayease_booking_email.html', {
                    'reservation': reservation,
                    'guest_name': guest_name,
                    'room': room,
                    'check_in': check_in,
                    'check_out': check_out,
                    'adults': adults,
                    'children': children,
                    'payment_method': payment_method,
                    'total_price': total_price,
                    'services': services,
                })

                email = EmailMultiAlternatives(
                    subject='Booking Confirmed - StayEase',
                    body='Your booking has been confirmed.',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[guest_email],
                )

                email.attach_alternative(html_content, "text/html")
                email.send()

                print("BOOKING EMAIL SENT SUCCESSFULLY")
                messages.success(request, "Booking successful! Reservation saved and confirmation email sent.")

            except Exception as e:
                print("BOOKING EMAIL FAILED:", e)
                messages.success(request, "Booking successful and reservation saved, but email was not sent.")

        else:
            messages.success(request, "Booking successful.")

        return redirect(f'/homepage/?booking_id={reservation.booking_id}#homePage')

    return render(request, 'booking.html', {
        'room': room
    })

def homepage(request):
    return my_reservations(request)

def submit_review(request, booking_id):
    if request.method == 'POST':
        reservation = Reservation.objects.filter(booking_id=booking_id).first()

        if not reservation:
            messages.error(request, "Reservation not found. Please refresh the page and try again.")
            return redirect('/#reservationsPage')

        rating_value = request.POST.get('rating')
        comment = request.POST.get('comment')

        Rating.objects.update_or_create(
            reservation=reservation,
            defaults={
                'guest': reservation.guest,
                'room': reservation.room,
                'rating': rating_value,
                'comments': comment,
            }
        )

        messages.success(request, "Review submitted successfully.")
        return redirect('/#reservationsPage')

    return redirect('/#homePage')


def my_reservations(request):
    user_id = request.session.get('user_id')

    if not user_id:
        messages.error(request, "Please log in first.")
        return redirect('/#loginPage')

    guest = Register.objects.get(id=user_id)
    today = date.today()

    upcoming_reservations = Reservation.objects.filter(
        guest=guest,
        check_out__gt=today
    ).exclude(status="Cancelled")

    past_reservations = Reservation.objects.filter(
        guest=guest,
        check_out__lte=today
    ).exclude(status="Cancelled")

    cancelled_reservations = Reservation.objects.filter(
        guest=guest,
        status="Cancelled"
    ).order_by('-booking_id')

    return render(request, 'finalhtml.html', {
        'upcoming_reservations': upcoming_reservations,
        'past_reservations': past_reservations,
        'cancelled_reservations': cancelled_reservations,
        'rooms': Room.objects.all(),
        'latest_booking_id': (Reservation.objects.order_by('-booking_id').first().booking_id if Reservation.objects.order_by('-booking_id').first() else 0),
    })


def cancel_reservation(request, booking_id):
    reservation = Reservation.objects.order_by('-booking_id').first()

    if reservation:
        Payment.objects.filter(reservation=reservation).delete()
        Rating.objects.filter(reservation=reservation).delete()
        reservation.delete()

    messages.success(request, "Reservation cancelled successfully.")
    return redirect('/#reservationsPage')