from django.shortcuts import render, redirect, get_object_or_404
from django.core.mail import send_mail
from django.contrib import messages
from django.conf import settings
from .models import Register, Room, Reservation, Rating, Payment
import random
from datetime import date, datetime, timedelta


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
                        'message_type': message_type
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

    return render(request, 'finalhtml.html', {
        'message': message,
        'message_type': message_type
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

        else:
            messages.error(request, "Invalid OTP. Please try again.")

    return render(request, 'verify_otp.html')


def booking(request, room_id):
    room = get_object_or_404(Room, pk=room_id)
    room_type = room.room_type

    if request.method == 'POST':
        print("BOOKING FORM DATA:", request.POST)

        if room_type.available_rooms > 0:
            room_type.available_rooms -= 1
            room_type.save()

            room.room_status = "pending"
            room.save()

            guest_email = request.POST.get('email')
            guest_name = request.POST.get('fullname') or request.POST.get('name') or "Guest"
            services = request.POST.get('services') or "No additional services selected"

            check_in = (
                request.POST.get('check_in')
                or request.POST.get('checkin')
                or request.POST.get('checkIn')
                or date.today()
            )

            check_out = (
                request.POST.get('check_out')
                or request.POST.get('checkout')
                or request.POST.get('checkOut')
                or date.today()
            )

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

            print("RESERVATION SAVED:", reservation)
            print("BOOKING EMAIL TO:", guest_email)

            if guest_email:
                try:
                    send_mail(
                        'Booking Confirmed - StayEase',
                        f'''
Hello {guest_name},

Your booking has been confirmed.

==============================
         BOOKING DETAILS
==============================

Booking ID:
{reservation.booking_id}

Room Booked:
{room.room_type}

Room Number:
{room.room_number}

Check-in:
{check_in}

Check-out:
{check_out}

Amount Paid:
₱{total_price}

Payment Method:
{payment_method}

Services:
{services}

Booking Status:
Pending Confirmation

Thank you for choosing StayEase.
''',
                        settings.DEFAULT_FROM_EMAIL,
                        [guest_email],
                        fail_silently=False,
                    )

                    print("BOOKING EMAIL SENT SUCCESSFULLY")
                    messages.success(request, "Booking successful! Reservation saved and confirmation email sent.")

                except Exception as e:
                    print("BOOKING EMAIL FAILED:", e)
                    messages.success(request, "Booking successful and reservation saved, but email was not sent.")

            else:
                print("NO EMAIL RECEIVED FROM FORM")
                messages.success(request, "Booking successful and reservation saved, but no email was provided.")

            return redirect('/#homePage')

        else:
            messages.error(request, "No rooms available for this room type.")
            return redirect('/#homePage')

    return render(request, 'booking.html', {
        'room': room
    })


def homepage(request):
    return redirect('/#homePage')

def submit_review(request, booking_id):
    if request.method == 'POST':
        reservation = get_object_or_404(Reservation, booking_id=booking_id)

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

    return render(request, 'finalhtml1.html', {
        'upcoming_reservations': upcoming_reservations,
        'past_reservations': past_reservations,
        'cancelled_reservations': cancelled_reservations,
    })

def popular(request):
    return render(request, 'finalhtml.html'), {
        'is_logged_in': request.session.get('user_id') is not None,
        'open_page': 'popularPage'
    }