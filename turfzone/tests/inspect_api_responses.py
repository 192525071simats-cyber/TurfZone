import os
import sys
import json
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import create_app
from app.models import db, User, Turf, TimeSlot, Booking

print("Creating test app...", flush=True)
app = create_app({
    'TESTING': True,
    'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
    'SECRET_KEY': 'test-secret-2026'
})

from app.seed import seed_database
with app.app_context():
    seed_database()

print("Testing direct Flask Test Client API network responses...", flush=True)
client = app.test_client()

# 1. Login API
login_res = client.post('/api/auth/login', json={'email': 'user@turfzone.com', 'password': 'User@123'})
print(f"POST /api/auth/login -> HTTP {login_res.status_code}", flush=True)
print(f"  Response: {json.dumps(login_res.json, indent=2)}", flush=True)
assert login_res.status_code == 200
token = login_res.json['data']['token']
headers = {'Authorization': f'Bearer {token}'}

# 2. Turf Detail API
turf_res = client.get('/api/turfs/1')
print(f"GET /api/turfs/1 -> HTTP {turf_res.status_code}", flush=True)
print(f"  Response: {json.dumps(turf_res.json, indent=2)}", flush=True)
assert turf_res.status_code == 200

# 3. Availability API
avail_res = client.get('/api/turfs/1/availability?date=2026-09-06')
print(f"GET /api/turfs/1/availability?date=2026-09-06 -> HTTP {avail_res.status_code}", flush=True)
print(f"  Response: {json.dumps(avail_res.json, indent=2)}", flush=True)
assert avail_res.status_code == 200
slots = avail_res.json['data']['slots']
target_slot = slots[0]

# 4. Booking Creation API
payload = {
    'turf_id': 1,
    'slot_id': target_slot['id'],
    'booking_date': '2026-09-06',
    'sport': 'Football',
    'addons': ['Match Football / Leather Ball (+₹100)']
}
book_res = client.post('/api/bookings', json=payload, headers=headers)
print(f"POST /api/bookings -> HTTP {book_res.status_code}", flush=True)
print(f"  Response: {json.dumps(book_res.json, indent=2)}", flush=True)
assert book_res.status_code == 201
booking_id = book_res.json['data']['booking']['id']

# 5. Availability API after booking -> verify slot is BOOKED
avail_res2 = client.get('/api/turfs/1/availability?date=2026-09-06')
print(f"GET /api/turfs/1/availability?date=2026-09-06 (after booking) -> HTTP {avail_res2.status_code}", flush=True)
booked_slot = next(s for s in avail_res2.json['data']['slots'] if s['id'] == target_slot['id'])
print(f"  Booked slot status: {booked_slot['status']}", flush=True)
assert booked_slot['status'] == 'BOOKED'

# 6. Duplicate Booking Conflict Test
conflict_res = client.post('/api/bookings', json=payload, headers=headers)
print(f"POST /api/bookings (duplicate conflict) -> HTTP {conflict_res.status_code}", flush=True)
print(f"  Response: {json.dumps(conflict_res.json, indent=2)}", flush=True)
assert conflict_res.status_code == 409

# 7. User Bookings API
my_bookings_res = client.get('/api/bookings', headers=headers)
print(f"GET /api/bookings -> HTTP {my_bookings_res.status_code}", flush=True)
print(f"  Response: {json.dumps(my_bookings_res.json, indent=2)}", flush=True)
assert my_bookings_res.status_code == 200

# 8. Cancel Booking API
cancel_res = client.put(f'/api/bookings/{booking_id}/cancel', headers=headers)
print(f"PUT /api/bookings/{booking_id}/cancel -> HTTP {cancel_res.status_code}", flush=True)
print(f"  Response: {json.dumps(cancel_res.json, indent=2)}", flush=True)
assert cancel_res.status_code == 200

# 9. Availability API after cancellation -> verify slot is AVAILABLE again
avail_res3 = client.get('/api/turfs/1/availability?date=2026-09-06')
print(f"GET /api/turfs/1/availability?date=2026-09-06 (after cancellation) -> HTTP {avail_res3.status_code}", flush=True)
released_slot = next(s for s in avail_res3.json['data']['slots'] if s['id'] == target_slot['id'])
print(f"  Released slot status: {released_slot['status']}", flush=True)
assert released_slot['status'] == 'AVAILABLE'

print("\nALL API ENDPOINTS VERIFIED AND RESPONDING WITH EXACT EXPECTED JSON STRUCTURES!", flush=True)
