Combined StayEase Django Project
================================

This folder combines:
1. Existing login/register StayEase project
2. OTP verification feature

How registration now works:
- User submits Sign Up form.
- Django generates a 6-digit OTP.
- Registration details are temporarily stored in session.
- User goes to /verify-otp/.
- If OTP is correct, the Register record is saved to the database.

How login works:
- User can log in using username or email.
- Correct password redirects to /#homePage.
- Wrong username/email or password shows an error message.

Important:
- OTP is printed in the terminal every time for easy testing.
- To send OTP by Gmail, configure environment variables:
  STAYEASE_EMAIL_USER=your_email@gmail.com
  STAYEASE_EMAIL_PASSWORD=your_gmail_app_password

Run steps:
1. Open terminal in this folder.
2. python manage.py makemigrations
3. python manage.py migrate
4. python manage.py createsuperuser
5. python manage.py runserver
6. Open http://127.0.0.1:8000/

Files merged/changed:
- main/views.py
- main/urls.py
- main/admin.py
- templates/finalfinal1.html
- templates/verify_otp.html
- hotelproject/settings.py
