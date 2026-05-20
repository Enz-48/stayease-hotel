from django import forms
from .models import Guest, Reservation, Payment, Rating


class GuestRegisterForm(forms.ModelForm):
    """
    Registration form — maps to PAGE 2 (register) in uifinal3.html.
    Creates a Guest record in the GUEST table.
    We store login credentials in Django's session (not a separate user model).
    """
    username = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'placeholder': 'Username'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Password'})
    )
    contact_number = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={'placeholder': 'Contact Number'})
    )
    home_address = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={'placeholder': 'Home Address'})
    )

    class Meta:
        model = Guest
        fields = ['first_name', 'last_name', 'email_address']
        widgets = {
            'first_name': forms.TextInput(attrs={'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'Last Name'}),
            'email_address': forms.EmailInput(attrs={'placeholder': 'Email Address'}),
        }

    def clean_email_address(self):
        email = self.cleaned_data.get('email_address')
        if Guest.objects.filter(email_address=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email


class GuestLoginForm(forms.Form):
    """
    Login form — maps to PAGE 1 (login) in uifinal3.html.
    Authenticates against the GUEST table using email + session.
    """
    username_or_email = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'Username or Email', 'id': 'loginUsername'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Password', 'id': 'loginPassword'})
    )


class RoomSearchForm(forms.Form):
    """
    Search form — maps to PAGE 3 (home search box) in uifinal3.html.
    """
    checkin = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'id': 'checkin'})
    )
    checkout = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'id': 'checkout'})
    )
    adults = forms.IntegerField(
        min_value=1, max_value=20, initial=2,
        widget=forms.NumberInput(attrs={'id': 'homeAdults', 'placeholder': '0'})
    )
    children = forms.IntegerField(
        min_value=0, max_value=10, initial=0,
        widget=forms.NumberInput(attrs={'id': 'homeChildren', 'placeholder': '0'})
    )

    def clean(self):
        cleaned_data = super().clean()
        checkin = cleaned_data.get('checkin')
        checkout = cleaned_data.get('checkout')
        if checkin and checkout and checkout <= checkin:
            raise forms.ValidationError('Check-out date must be after check-in date.')
        return cleaned_data


class BookingForm(forms.Form):
    """
    Booking form — maps to PAGE 5 (booking details) in uifinal3.html.
    Collects guest info, service selections, bed type, room type upgrade, and payment method.
    """
    # Guest details section
    first_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'placeholder': 'John', 'id': 'guestFirstName'})
    )
    last_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'placeholder': 'Doe', 'id': 'guestLastName'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'placeholder': 'john@example.com', 'id': 'guestEmail'})
    )
    phone = forms.CharField(
        max_length=20, required=False,
        widget=forms.TextInput(attrs={'placeholder': '+63 912 345 6789', 'id': 'guestPhone'})
    )

    # Guest count
    adults = forms.IntegerField(min_value=1, max_value=50, initial=2,
        widget=forms.NumberInput(attrs={'id': 'bookingAdults'}))
    children = forms.IntegerField(min_value=0, max_value=20, initial=0,
        widget=forms.NumberInput(attrs={'id': 'bookingChildren'}))

    # Dates
    checkin = forms.DateField(widget=forms.HiddenInput())
    checkout = forms.DateField(widget=forms.HiddenInput())
    room_id = forms.IntegerField(widget=forms.HiddenInput())

    # Upgrades & preferences
    ROOM_TYPE_CHOICES = [
        ('Standard', 'Standard — Base Price'),
        ('Superior', 'Superior — +₱1,500/night'),
        ('Deluxe', 'Deluxe — +₱3,000/night'),
        ('Suite', 'Suite — +₱8,000/night'),
    ]
    BED_TYPE_CHOICES = [
        ('Twin', 'Twin Beds'),
        ('Queen', 'Queen Bed'),
        ('King', 'King Bed'),
        ('California King', 'California King'),
    ]
    PAYMENT_METHOD_CHOICES = [
        ('Credit Card', 'Credit Card'),
        ('Debit Card', 'Debit Card'),
        ('Cash', 'Cash'),
        ('GCash', 'GCash'),
        ('PayMaya', 'PayMaya'),
        ('Bank Transfer', 'Bank Transfer'),
    ]

    room_type_upgrade = forms.ChoiceField(choices=ROOM_TYPE_CHOICES, initial='Standard')
    bed_type = forms.ChoiceField(choices=BED_TYPE_CHOICES, initial='Twin')
    payment_method = forms.ChoiceField(choices=PAYMENT_METHOD_CHOICES)

    # Services (multi-select from SERVICE table)
    services = forms.MultipleChoiceField(
        required=False,
        widget=forms.CheckboxSelectMultiple(),
        choices=[]  # populated dynamically in view
    )

    def __init__(self, *args, service_choices=None, **kwargs):
        super().__init__(*args, **kwargs)
        if service_choices:
            self.fields['services'].choices = service_choices


class RatingForm(forms.ModelForm):
    """
    Rating form — for guests to submit ratings after checkout.
    Maps to RATINGS table.
    """
    class Meta:
        model = Rating
        fields = ['rating_service', 'rating_room', 'comments']
        widgets = {
            'rating_service': forms.NumberInput(attrs={'min': 1, 'max': 5, 'placeholder': '1-5'}),
            'rating_room': forms.NumberInput(attrs={'min': 1, 'max': 5, 'placeholder': '1-5'}),
            'comments': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Share your experience...'}),
        }
