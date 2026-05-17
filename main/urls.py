from django.urls import path
from . import views
app_name = 'hotel'
urlpatterns = [
    path('', views.home, name='home'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('homepage/', views.homepage, name='homepage'),
    path('booking/<int:room_id>/', views.booking, name='booking'),
    path('submit-review/<int:booking_id>/', views.submit_review, name='submit_review'),
    path('popular/', views.popular, name='popular'),
]
