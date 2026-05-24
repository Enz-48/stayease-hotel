from django.db import models


class Register(models.Model):
    firstname = models.CharField(max_length=100)
    lastname = models.CharField(max_length=100)
    email = models.EmailField()
    contact = models.CharField(max_length=20)
    address = models.CharField(max_length=255)
    username = models.CharField(max_length=100)
    password = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.firstname} {self.lastname}"


class RoomType(models.Model):
    type_name = models.CharField(max_length=100)
    available_rooms = models.IntegerField(default=10)

    def __str__(self):
        return self.type_name


class Room(models.Model):
    ROOM_STATUS_CHOICES = (
        ("vacant", "Vacant"),
        ("occupied", "Occupied"),
        ("maintenance", "Maintenance"),
        ("unavailable", "Unavailable"),
    )

    room_id = models.AutoField(primary_key=True)
    room_number = models.CharField(max_length=20)
    room_type = models.ForeignKey(RoomType, on_delete=models.CASCADE)
    bed_type = models.CharField(max_length=100, default="Single Bed")
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    room_status = models.CharField(max_length=20, choices=ROOM_STATUS_CHOICES, default="vacant")

    def __str__(self):
        return f"Room {self.room_number} - {self.room_type}"


class Reservation(models.Model):
    booking_id = models.AutoField(primary_key=True)
    guest = models.ForeignKey(Register, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    check_in = models.DateField()
    check_out = models.DateField()
    adults = models.IntegerField(default=1)
    children = models.IntegerField(default=0)
    status = models.CharField(max_length=30, default="Pending")

    def __str__(self):
        return f"Booking {self.booking_id} - {self.guest}"


class Service(models.Model):
    service_id = models.AutoField(primary_key=True)
    service_name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return self.service_name


class Payment(models.Model):
    transaction_no = models.AutoField(primary_key=True)
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE)
    payment_method = models.CharField(max_length=50)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_status = models.CharField(max_length=30, default="Unpaid")

    def __str__(self):
        return f"Payment {self.transaction_no} - {self.payment_status}"


class Rating(models.Model):
    reservation = models.OneToOneField(Reservation, on_delete=models.CASCADE, null=True, blank=True)
    guest = models.ForeignKey(Register, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    rating = models.IntegerField()
    comments = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.guest} - Room {self.room.room_number} - {self.rating}/5"