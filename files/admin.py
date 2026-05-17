from django.contrib import admin
from .models import Guest, Room, RoomType, Service, Reservation, Payment, Rating, ReservationService


@admin.register(Guest)
class GuestAdmin(admin.ModelAdmin):
    list_display = ('guest_id', 'first_name', 'last_name', 'email_address')
    search_fields = ('first_name', 'last_name', 'email_address')


@admin.register(RoomType)
class RoomTypeAdmin(admin.ModelAdmin):
    list_display = ('room_type_id', 'type_name')


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('room_id', 'room_type', 'room_price', 'amenities')
    list_filter = ('room_type',)


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('service_id', 'service_name', 'price', 'admin')


class PaymentInline(admin.StackedInline):
    model = Payment
    extra = 0


class ReservationServiceInline(admin.TabularInline):
    model = ReservationService
    extra = 0


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('booking_id', 'guest', 'room', 'check_in_date', 'check_out_date', 's_duration', 'cancel')
    list_filter = ('cancel', 'check_in_date')
    search_fields = ('guest__first_name', 'guest__last_name', 'guest__email_address')
    inlines = [PaymentInline, ReservationServiceInline]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('transaction_no', 'booking', 'total_amount', 'status', 'payment_method')
    list_filter = ('status', 'payment_method')


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('rating_id', 'guest', 'room', 'rating_service', 'rating_room')
