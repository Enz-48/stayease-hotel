# StayEase — Django Backend Setup Guide

## Project Structure
```
stayease/
├── stayease/
│   ├── settings.py       ← MySQL hotel_db config
│   ├── urls.py           ← Root routing
│   └── wsgi.py
├── hotel/
│   ├── models.py         ← All 8 tables mapped from hotel_db
│   ├── forms.py          ← Login, Register, Search, Booking forms
│   ├── views.py          ← All page views + JSON API
│   ├── urls.py           ← All routes
│   └── admin.py          ← Admin panel
├── templates/
│   ├── base.html
│   └── hotel/
│       ├── login.html          ← Page 1
│       ├── register.html       ← Page 2
│       ├── home.html           ← Page 3
│       ├── search.html         ← Page 4 (real room data from DB)
│       ├── booking.html        ← Page 5
│       └── booking_success.html
├── requirements.txt
└── seed_data.sql         ← Sample rooms & services for hotel_db
```

---

## How Your HTML Pages Map to Django Views

| HTML Page (uifinal3.html) | Django URL            | View Function        |
|---------------------------|-----------------------|----------------------|
| #loginPage                | `GET/POST /`          | `login_view`         |
| #registerPage             | `GET/POST /register/` | `register_view`      |
| #homePage                 | `GET /home/`          | `home_view`          |
| #searchPage               | `GET /rooms/`         | `search_view`        |
| #bookingPage              | `GET/POST /book/<id>/`| `booking_view`       |
| Success Modal             | `GET /booking/success/<id>/` | `booking_success_view` |

---

## Step 1 — Install Python packages

```bash
pip install -r requirements.txt
```

> **Windows MySQL fix:** If `mysqlclient` fails, use PyMySQL:
> ```bash
> pip install PyMySQL
> ```
> Add to `stayease/__init__.py`:
> ```python
> import pymysql
> pymysql.install_as_MySQLdb()
> ```

---

## Step 2 — Set up hotel_db in MySQL

Run your schema SQL first:
```bash
mysql -u root -p < hotel_db_schema.sql
```

Then load the seed data (rooms, services):
```bash
mysql -u root -p hotel_db < seed_data.sql
```

Update `stayease/settings.py` with your credentials:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'hotel_db',
        'USER': 'root',          # your MySQL user
        'PASSWORD': 'yourpass',  # your MySQL password
        'HOST': 'localhost',
        'PORT': '3306',
    }
}
```

---

## Step 3 — Run Django migrations (for sessions only)

Since your hotel tables already exist (`managed=False` in models), only run:
```bash
python manage.py migrate
```
This creates Django's session and admin tables without touching your hotel tables.

---

## Step 4 — Create Django superuser (for /admin panel)

```bash
python manage.py createsuperuser
```

---

## Step 5 — Copy your stayease.css

Place your CSS file at:
```
stayease/static/stayease.css
```

---

## Step 6 — Run the server

```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000/` → Login page.

---

## How the DB Tables Are Used

| Table                | Used in                                      |
|----------------------|----------------------------------------------|
| `GUEST`              | Register, Login (session), Booking           |
| `ROOM`               | Search page (availability by dates)          |
| `ROOM_TYPE`          | Room cards (type name display)               |
| `SERVICE`            | Booking page (service grid from DB)          |
| `RESERVATION`        | Created on booking confirm                   |
| `PAYMENT`            | Created alongside reservation (status: Pending) |
| `RESERVATION_SERVICE`| Many-to-many services linked to reservation  |
| `RATINGS`            | Available via admin panel                    |
| `ADMIN`              | Django admin panel (`/admin/`)               |

---

## JSON API for your HTML frontend (AJAX)

If you want to call from your original HTML file:

```javascript
// Get real room availability for dates
fetch('/api/rooms/?checkin=2024-12-09&checkout=2024-12-12')
  .then(r => r.json())
  .then(data => {
      data.rooms.forEach(room => {
          console.log(room.room_id, room.status, room.price);
      });
  });
```

Response format:
```json
{
  "rooms": [
    { "room_id": 1, "room_type": "Deluxe", "price": 8500.0, "amenities": "...", "status": "vacant" },
    { "room_id": 2, "room_type": "Superior", "price": 5500.0, "amenities": "...", "status": "occupied" }
  ]
}
```
