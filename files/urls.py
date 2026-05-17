from django.urls import path
from . import views

app_name = 'hotel'

urlpatterns = [
    # Auth
    path('', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),

    # Main pages
    path('home/', views.home_view, name='home'),
    path('rooms/', views.search_view, name='search'),
    path('book/<int:room_id>/', views.booking_view, name='booking'),
    path('booking/success/<int:booking_id>/', views.booking_success_view, name='booking_success'),

    # JSON API for AJAX
    path('api/rooms/', views.room_availability_api, name='rooms_api'),
]
