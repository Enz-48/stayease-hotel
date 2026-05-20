-- ======================
-- SEED DATA for StayEase
-- Run this AFTER your schema SQL
-- ======================
USE hotel_db;

-- Room Types (matching types shown in uifinal3.html)
INSERT INTO ROOM_TYPE (Type_Name) VALUES
  ('Standard'),
  ('Superior'),
  ('Deluxe'),
  ('Suite'),
  ('Family Room');

-- Rooms (matching rooms shown in the HTML: 101, 102, 103, 104, 105, 106)
INSERT INTO ROOM (Room_type_ID, Room_price, Amenities) VALUES
  (3, 8500.00,  'Ocean view • King bed • Mini bar • Balcony'),            -- Room 1 = Deluxe
  (2, 5500.00,  'City view • Twin beds • Work desk • Coffee maker'),       -- Room 2 = Superior
  (4, 18000.00, 'Panoramic view • Living room • Jacuzzi • Butler service'),-- Room 3 = Suite
  (1, 3200.00,  'Standard amenities • Queen bed • Free Wi-Fi'),            -- Room 4 = Standard
  (5, 15000.00, 'Connecting rooms • Kids amenities • Game console • Mini fridge'), -- Room 5 = Family
  (2, 7200.00,  'Mountain view • Balcony • Premium amenities • Bathrobe'); -- Room 6 = Superior

-- Services (matching the service options in the HTML booking page)
INSERT INTO SERVICE (Service_Name, Price, Admin_ID) VALUES
  ('Breakfast',          500.00,  NULL),
  ('Spa Access',         800.00,  NULL),
  ('Airport Transfer',  1200.00,  NULL),
  ('Extra Cleaning',     600.00,  NULL),
  ('Premium Wi-Fi',     1500.00,  NULL),
  ('Room Service',      2000.00,  NULL),
  ('Gym Access',        1000.00,  NULL),
  ('Pool Access',       2500.00,  NULL),
  ('Mini Bar',          1800.00,  NULL),
  ('Babysitting',       3000.00,  NULL);

-- Admin account (password should be hashed in production)
INSERT INTO ADMIN (Admin_user, Admin_password, Phone_No) VALUES
  ('admin', 'changeme_hashed_password', '+63-912-000-0001');
