import unittest
from datetime import date, timedelta
from app import create_app
from app.models import db, User, Turf, TimeSlot, Booking

class TestCompleteBookingFlow(unittest.TestCase):
    def setUp(self):
        self.app = create_app({
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'SECRET_KEY': 'test-secret-key-2026'
        })
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()

            # Create Users
            admin = User(name="Admin User", email="admin@turfzone.com", phone="+91 9876543210", role="ADMIN", is_active=True)
            admin.set_password("Admin@123")
            user1 = User(name="Dhanesh Kumar", email="user@turfzone.com", phone="+91 9840123456", role="USER", is_active=True)
            user1.set_password("User@123")
            user2 = User(name="Rahul Sharma", email="rahul@turfzone.com", phone="+91 9962001122", role="USER", is_active=True)
            user2.set_password("User@123")
            db.session.add_all([admin, user1, user2])

            # Create Turf
            turf = Turf(
                name="Marina Champions Arena",
                location="Triplicane, Chennai",
                address="45 Marina Beach Expressway, Chennai",
                sport="Football, Cricket",
                description="Premium FIFA-standard synthetic turf.",
                facilities="Floodlights, Parking, Changing Rooms",
                price_per_hour=1200.0,
                rating=4.9,
                reviews_count=86,
                image_url="https://images.unsplash.com/photo-1529900245534-47fbf8221565",
                is_active=True
            )
            db.session.add(turf)
            db.session.commit()

            # Create Slots
            slot_times = [
                ("06:00", "07:00"),
                ("07:00", "08:00"),
                ("18:00", "19:00"),
                ("19:00", "20:00")
            ]
            for st, et in slot_times:
                s = TimeSlot(turf_id=turf.id, start_time=st, end_time=et)
                db.session.add(s)
            db.session.commit()

    def test_complete_booking_and_cancellation_lifecycle(self):
        # 1. User 1 Login
        login_res = self.client.post('/api/auth/login', json={
            'email': 'user@turfzone.com',
            'password': 'User@123'
        })
        self.assertEqual(login_res.status_code, 200)
        token1 = login_res.json['data']['token']
        headers1 = {'Authorization': f'Bearer {token1}'}

        # 2. Turf Detail retrieval
        turf_res = self.client.get('/api/turfs/1')
        self.assertEqual(turf_res.status_code, 200)
        self.assertEqual(turf_res.json['data']['turf']['name'], 'Marina Champions Arena')

        # 3. Select Date (Tomorrow) and check available slots
        tomorrow = (date.today() + timedelta(days=1)).strftime('%Y-%m-%d')
        avail_res = self.client.get(f'/api/turfs/1/availability?date={tomorrow}')
        self.assertEqual(avail_res.status_code, 200)
        avail_data = avail_res.json['data']
        self.assertEqual(avail_data['total_slots'], 4)
        self.assertEqual(avail_data['available_slots'], 4)
        self.assertEqual(avail_data['booked_slots'], 0)
        slots = avail_data['slots']
        self.assertEqual(len(slots), 4)
        self.assertTrue(all(s['status'] == 'AVAILABLE' for s in slots))

        # 4. User 1 books the 18:00-19:00 slot with Add-on equipment
        target_slot = next(s for s in slots if s['start_time'] == '18:00')
        booking_payload = {
            'turf_id': 1,
            'slot_id': target_slot['id'],
            'booking_date': tomorrow,
            'sport': 'Football',
            'addons': ['Match Football / Leather Ball (+₹100)', 'Team Bibs & Vests (+₹150)']
        }
        create_res = self.client.post('/api/bookings', json=booking_payload, headers=headers1)
        self.assertEqual(create_res.status_code, 201)
        booking = create_res.json['data']['booking']
        self.assertTrue(booking['booking_reference'].startswith('TZ-'))
        self.assertEqual(booking['turf_name'], 'Marina Champions Arena')
        self.assertEqual(booking['slot_time'], '18:00 - 19:00')
        self.assertEqual(booking['price'], 1450.0)  # 1200 + 100 + 150
        self.assertEqual(booking['status'], 'CONFIRMED')
        booking_id = booking['id']

        # 5. Verify in database directly
        with self.app.app_context():
            db_booking = db.session.get(Booking, booking_id)
            self.assertIsNotNone(db_booking)
            self.assertEqual(db_booking.status, 'CONFIRMED')
            self.assertEqual(db_booking.price, 1450.0)

        # 6. Verify My Bookings for User 1
        my_bookings_res = self.client.get('/api/bookings', headers=headers1)
        self.assertEqual(my_bookings_res.status_code, 200)
        my_bookings = my_bookings_res.json['data']['bookings']
        self.assertEqual(len(my_bookings), 1)
        self.assertEqual(my_bookings[0]['id'], booking_id)
        self.assertEqual(my_bookings[0]['booking_reference'], booking['booking_reference'])

        # 7. Check availability again: Booked slot must now be BOOKED and unavailable
        avail_res2 = self.client.get(f'/api/turfs/1/availability?date={tomorrow}')
        self.assertEqual(avail_res2.status_code, 200)
        avail_data2 = avail_res2.json['data']
        self.assertEqual(avail_data2['available_slots'], 3)
        self.assertEqual(avail_data2['booked_slots'], 1)
        slot_status_map = {s['id']: s['status'] for s in avail_data2['slots']}
        self.assertEqual(slot_status_map[target_slot['id']], 'BOOKED')

        # 8. User 2 logs in and attempts to book the SAME slot (Conflict Test)
        login_res2 = self.client.post('/api/auth/login', json={
            'email': 'rahul@turfzone.com',
            'password': 'User@123'
        })
        self.assertEqual(login_res2.status_code, 200)
        token2 = login_res2.json['data']['token']
        headers2 = {'Authorization': f'Bearer {token2}'}

        conflict_res = self.client.post('/api/bookings', json={
            'turf_id': 1,
            'slot_id': target_slot['id'],
            'booking_date': tomorrow,
            'sport': 'Cricket'
        }, headers=headers2)
        self.assertEqual(conflict_res.status_code, 409)
        self.assertEqual(conflict_res.json['error'], 'BOOKING_CONFLICT')

        # 9. User 1 cancels the booking
        cancel_res = self.client.put(f'/api/bookings/{booking_id}/cancel', headers=headers1)
        self.assertEqual(cancel_res.status_code, 200)
        self.assertEqual(cancel_res.json['data']['booking']['status'], 'CANCELLED')

        # 10. Check availability after cancellation: Slot must be AVAILABLE again
        avail_res3 = self.client.get(f'/api/turfs/1/availability?date={tomorrow}')
        self.assertEqual(avail_res3.status_code, 200)
        avail_data3 = avail_res3.json['data']
        self.assertEqual(avail_data3['available_slots'], 4)
        self.assertEqual(avail_data3['booked_slots'], 0)
        slot_status_map3 = {s['id']: s['status'] for s in avail_data3['slots']}
        self.assertEqual(slot_status_map3[target_slot['id']], 'AVAILABLE')

        # 11. User 2 can now successfully book the released slot
        book_res2 = self.client.post('/api/bookings', json={
            'turf_id': 1,
            'slot_id': target_slot['id'],
            'booking_date': tomorrow,
            'sport': 'Cricket'
        }, headers=headers2)
        self.assertEqual(book_res2.status_code, 201)
        self.assertEqual(book_res2.json['data']['booking']['sport'], 'Cricket')

    def test_past_date_and_validation(self):
        login_res = self.client.post('/api/auth/login', json={'email': 'user@turfzone.com', 'password': 'User@123'})
        token = login_res.json['data']['token']
        headers = {'Authorization': f'Bearer {token}'}

        yesterday = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')
        res = self.client.post('/api/bookings', json={
            'turf_id': 1,
            'slot_id': 1,
            'booking_date': yesterday,
            'sport': 'Football'
        }, headers=headers)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json['error'], 'PAST_DATE')

if __name__ == '__main__':
    unittest.main()
