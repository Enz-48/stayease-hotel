"""
Models mapped directly to the hotel_db MySQL schema.
We use managed=False so Django doesn't try to recreate existing tables.
Set managed=True only if you want Django to manage migrations.
"""
from django.db import models


class Admin(models.Model):
    """Maps to ADMIN table."""
    admin_id = models.AutoField(primary_key=True, db_column='Admin_ID')
    admin_user = models.CharField(max_length=50, db_column='Admin_user')
    admin_password = models.CharField(max_length=100, db_column='Admin_password')  # store hashed
    phone_no = models.CharField(max_length=20, blank=True, null=True, db_column='Phone_No')

    class Meta:
        db_table = 'ADMIN'
        managed = False  # Table already exists in hotel_db

    def __str__(self):
        return self.admin_user


class Guest(models.Model):
    """Maps to GUEST table."""
    guest_id = models.AutoField(primary_key=True, db_column='Guest_ID')
    first_name = models.CharField(max_length=50, db_column='First_Name')
    last_name = models.CharField(max_length=50, db_column='Last_Name')
    email_address = models.EmailField(max_length=100, unique=True, db_column='Email_Address')

    class Meta:
        db_table = 'GUEST'
        managed = False

    def __str__(self):
        return f'{self.first_name} {self.last_name}'

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'


class RoomType(models.Model):
    """Maps to ROOM_TYPE table."""
    room_type_id = models.AutoField(primary_key=True, db_column='Room_type_ID')
    type_name = models.CharField(max_length=50, db_column='Type_Name')

    class Meta:
        db_table = 'ROOM_TYPE'
        managed = False

    def __str__(self):
        return self.type_name


class Room(models.Model):
    """Maps to ROOM table."""
    room_id = models.AutoField(primary_key=True, db_column='Room_ID')
    room_type = models.ForeignKey(
        RoomType, on_delete=models.SET_NULL, null=True,
        db_column='Room_type_ID', related_name='rooms'
    )
    room_price = models.DecimalField(max_digits=10, decimal_places=2, db_column='Room_price')
    amenities = models.TextField(blank=True, null=True, db_column='Amenities')

    class Meta:
        db_table = 'ROOM'
        managed = False

    def __str__(self):
        return f'Room {self.room_id} ({self.room_type})'

    def get_status(self, checkin, checkout):
        """
        Determine room status for a given date range.
        Returns: 'vacant', 'occupied', 'pending', or 'received'
        """
        from datetime import date
        reservations = self.reservations.filter(
            cancel=False,
            check_in_date__lt=checkout,
            check_out_date__gt=checkin,
        )
        if not reservations.exists():
            return 'vacant'
        latest = reservations.order_by('-booking_id').first()
        payment = Payment.objects.filter(booking=latest).first()
        if payment:
            if payment.status == 'Confirmed':
                return 'received'
            elif payment.status == 'Pending':
                return 'pending'
        return 'occupied'


class Service(models.Model):
    """Maps to SERVICE table."""
    service_id = models.AutoField(primary_key=True, db_column='Service_ID')
    service_name = models.CharField(max_length=100, db_column='Service_Name')
    price = models.DecimalField(max_digits=10, decimal_places=2, db_column='Price')
    admin = models.ForeignKey(
        Admin, on_delete=models.SET_NULL, null=True,
        db_column='Admin_ID', related_name='services'
    )

    class Meta:
        db_table = 'SERVICE'
        managed = False

    def __str__(self):
        return f'{self.service_name} (₱{self.price})'


class Reservation(models.Model):
    """Maps to RESERVATION table."""
    booking_id = models.AutoField(primary_key=True, db_column='Booking_ID')
    check_in_date = models.DateField(db_column='Check_in_Date')
    check_out_date = models.DateField(db_column='Check_out_Date')
    s_duration = models.IntegerField(blank=True, null=True, db_column='S_Duration')
    cancel = models.BooleanField(default=False, db_column='Cancel')
    guest = models.ForeignKey(
        Guest, on_delete=models.CASCADE, null=True,
        db_column='Guest_ID', related_name='reservations'
    )
    admin = models.ForeignKey(
        Admin, on_delete=models.SET_NULL, null=True, blank=True,
        db_column='Admin_ID', related_name='reservations'
    )
    room = models.ForeignKey(
        Room, on_delete=models.CASCADE, null=True,
        db_column='Room_ID', related_name='reservations'
    )
    services = models.ManyToManyField(
        Service,
        through='ReservationService',
        related_name='reservations'
    )

    class Meta:
        db_table = 'RESERVATION'
        managed = False

    def __str__(self):
        return f'Booking #{self.booking_id} — {self.guest}'

    def calculate_duration(self):
        return (self.check_out_date - self.check_in_date).days

    def save(self, *args, **kwargs):
        self.s_duration = self.calculate_duration()
        super().save(*args, **kwargs)


class Payment(models.Model):
    """Maps to PAYMENT table."""
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Confirmed', 'Confirmed'),
        ('Failed', 'Failed'),
        ('Refunded', 'Refunded'),
    ]
    METHOD_CHOICES = [
        ('Credit Card', 'Credit Card'),
        ('Debit Card', 'Debit Card'),
        ('Cash', 'Cash'),
        ('GCash', 'GCash'),
        ('PayMaya', 'PayMaya'),
        ('Bank Transfer', 'Bank Transfer'),
    ]
    transaction_no = models.AutoField(primary_key=True, db_column='Transaction_No')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, db_column='Total_amount')
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, blank=True, null=True, db_column='Status')
    payment_method = models.CharField(max_length=50, choices=METHOD_CHOICES, blank=True, null=True, db_column='Payment_Method')
    booking = models.ForeignKey(
        Reservation, on_delete=models.CASCADE, null=True,
        db_column='Booking_ID', related_name='payments'
    )

    class Meta:
        db_table = 'PAYMENT'
        managed = False

    def __str__(self):
        return f'Payment #{self.transaction_no} — ₱{self.total_amount}'


class Rating(models.Model):
    """Maps to RATINGS table."""
    rating_id = models.AutoField(primary_key=True, db_column='Rating_ID')
    rating_service = models.IntegerField(blank=True, null=True, db_column='Rating_Service')
    rating_room = models.IntegerField(blank=True, null=True, db_column='Rating_Room')
    comments = models.TextField(blank=True, null=True, db_column='Comments')
    guest = models.ForeignKey(
        Guest, on_delete=models.CASCADE, null=True,
        db_column='Guest_ID', related_name='ratings'
    )
    room = models.ForeignKey(
        Room, on_delete=models.CASCADE, null=True,
        db_column='Room_ID', related_name='ratings'
    )

    class Meta:
        db_table = 'RATINGS'
        managed = False

    def __str__(self):
        return f'Rating #{self.rating_id} by {self.guest}'


class ReservationService(models.Model):
    """Maps to RESERVATION_SERVICE (many-to-many through table)."""
    booking = models.ForeignKey(Reservation, on_delete=models.CASCADE, db_column='Booking_ID')
    service = models.ForeignKey(Service, on_delete=models.CASCADE, db_column='Service_ID')

    class Meta:
        db_table = 'RESERVATION_SERVICE'
        managed = False
        unique_together = (('booking', 'service'),)
