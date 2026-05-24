from django.urls import path
from . import views
app_name = 'hotel'

urlpatterns = [
    path('', views.home, name='home'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('homepage/', views.homepage, name='homepage'),
    path('booking/<int:room_id>/', views.booking, name='booking'),
    path('submit-review/<int:booking_id>/', views.submit_review, name='submit_review'),


    path("my-reservations/", views.my_reservations, name="my_reservations"),

    path("forgot-password/", views.forgot_password, name="forgot_password"),
    path("verify-reset-otp/", views.verify_reset_otp, name="verify_reset_otp_page"),
    path("reset-password/", views.reset_password, name="reset_password"),
    path("cancel-reservation/<int:booking_id>/", views.cancel_reservation, name="cancel_reservation"),


]
