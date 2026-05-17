from django.contrib import admin
from .models import Register, RoomType, Room, Reservation, Service, Payment, Rating

admin.site.register(Register)
admin.site.register(RoomType)
admin.site.register(Room)
admin.site.register(Reservation)
admin.site.register(Service)
admin.site.register(Payment)
admin.site.register(Rating)