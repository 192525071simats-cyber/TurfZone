import unittest
from datetime import date, timedelta
from app import create_app
from app.models import db, User, Turf, TimeSlot, Booking, Tournament, TournamentRegistration
from app.auth import generate_token


class TurfZoneTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app({
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'SECRET_KEY': 'test-secret-key-123'
        })
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

        # Seed initial test data
        self.setup_test_data()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def setup_test_data(self):
        # Admin User
        self.admin = User(
            name="Admin User",
            email="admin@test.com",
            phone="9876543210",
            role="ADMIN"
        )
        self.admin.set_password("Admin@123")
        db.session.add(self.admin)

        # Normal User 1
        self.user1 = User(
            name="Player One",
            email="player1@test.com",
            phone="9840001122",
            role="USER"
        )
        self.user1.set_password("User@123")
        db.session.add(self.user1)

        # Normal User 2
        self.user2 = User(
            name="Player Two",
            email="player2@test.com",
            phone="9840003344",
            role="USER"
        )
        self.user2.set_password("User@123")
        db.session.add(self.user2)

        db.session.commit()

        # Generate tokens
        self.admin_token = generate_token(self.admin.id, 'ADMIN')
        self.user1_token = generate_token(self.user1.id, 'USER')
        self.user2_token = generate_token(self.user2.id, 'USER')

        # Create Turf
        self.turf = Turf(
            name="Chennai Test Arena",
            location="Velachery, Chennai",
            address="12 Bypass Road, Velachery",
            sport="Football, Cricket",
            description="High quality test turf",
            facilities="Floodlights, Parking, Washrooms",
            price_per_hour=1000.0,
            rating=4.9,
            reviews_count=10,
            image_url="https://images.unsplash.com/photo-1529900245534-47fbf8221565",
            is_active=True
        )
        db.session.add(self.turf)
        db.session.commit()

        # Create Slots
        self.slot1 = TimeSlot(turf_id=self.turf.id, start_time="09:00", end_time="10:00")
        self.slot2 = TimeSlot(turf_id=self.turf.id, start_time="10:00", end_time="11:00")
        db.session.add_all([self.slot1, self.slot2])
        db.session.commit()

        # Create Tournament
        today = date.today()
        self.tournament = Tournament(
            name="Chennai Test Cup",
            sport="Football",
            description="Test knockout tournament",
            venue=self.turf.name,
            tournament_date=today + timedelta(days=10),
            registration_deadline=today + timedelta(days=5),
            entry_fee=1500.0,
            max_teams=2,
            status="OPEN",
            image_url="https://images.unsplash.com/photo-1579952363873-27f3bade9f55"
        )
        db.session.add(self.tournament)
        db.session.commit()

    # =========================================================================
    # 1. AUTHENTICATION TESTS
    # =========================================================================
    def test_user_registration(self):
        res = self.client.post('/api/auth/register', json={
            'name': 'New Athlete',
            'email': 'newathlete@test.com',
            'phone': '9123456789',
            'password': 'Password@123',
            'confirm_password': 'Password@123'
        })
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['user']['email'], 'newathlete@test.com')

    def test_duplicate_email_registration(self):
        res = self.client.post('/api/auth/register', json={
            'name': 'Duplicate User',
            'email': 'player1@test.com',
            'phone': '9123456789',
            'password': 'Password@123',
            'confirm_password': 'Password@123'
        })
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertFalse(data['success'])
        self.assertEqual(data['error'], 'DUPLICATE_EMAIL')

    def test_user_login(self):
        res = self.client.post('/api/auth/login', json={
            'email': 'player1@test.com',
            'password': 'User@123'
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertIn('token', data['data'])

    def test_invalid_login(self):
        res = self.client.post('/api/auth/login', json={
            'email': 'player1@test.com',
            'password': 'WrongPassword'
        })
        self.assertEqual(res.status_code, 401)
        data = res.get_json()
        self.assertFalse(data['success'])

    def test_protected_route_without_token(self):
        res = self.client.get('/api/auth/me')
        self.assertEqual(res.status_code, 401)

    def test_protected_route_with_token(self):
        res = self.client.get('/api/auth/me', headers={
            'Authorization': f'Bearer {self.user1_token}'
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['data']['user']['email'], 'player1@test.com')

    # =========================================================================
    # 2. TURF TESTS
    # =========================================================================
    def test_get_turfs(self):
        res = self.client.get('/api/turfs')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertGreaterEqual(len(data['data']['turfs']), 1)

    def test_get_turf_details(self):
        res = self.client.get(f'/api/turfs/{self.turf.id}')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['data']['turf']['name'], 'Chennai Test Arena')
        self.assertIn('slots', data['data']['turf'])

    def test_admin_create_turf(self):
        res = self.client.post('/api/turfs', json={
            'name': 'Anna Nagar Turf',
            'location': 'Anna Nagar, Chennai',
            'address': '55 Roundtana, Anna Nagar',
            'sport': 'Football',
            'description': 'Brand new turf in Anna Nagar',
            'facilities': 'Floodlights, Changing rooms',
            'price_per_hour': 1200.0
        }, headers={'Authorization': f'Bearer {self.admin_token}'})
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['turf']['name'], 'Anna Nagar Turf')

    def test_non_admin_cannot_create_turf(self):
        res = self.client.post('/api/turfs', json={
            'name': 'Unauthorized Turf',
            'location': 'Velachery',
            'address': '123 Fake St',
            'sport': 'Football',
            'description': 'Should fail',
            'price_per_hour': 1000.0
        }, headers={'Authorization': f'Bearer {self.user1_token}'})
        self.assertEqual(res.status_code, 403)

    # =========================================================================
    # 3. BOOKING CONFLICT & CANCELLATION TESTS (CRITICAL REQUIREMENT)
    # =========================================================================
    def test_booking_availability(self):
        tomorrow = (date.today() + timedelta(days=1)).strftime('%Y-%m-%d')
        res = self.client.get(f'/api/turfs/{self.turf.id}/availability?date={tomorrow}')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['data']['total_slots'], 2)
        self.assertEqual(data['data']['available_slots'], 2)

    def test_successful_booking_creation(self):
        booking_date = (date.today() + timedelta(days=2)).strftime('%Y-%m-%d')
        res = self.client.post('/api/bookings', json={
            'turf_id': self.turf.id,
            'slot_id': self.slot1.id,
            'booking_date': booking_date,
            'sport': 'Football'
        }, headers={'Authorization': f'Bearer {self.user1_token}'})

        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertTrue(data['data']['booking']['booking_reference'].startswith('TZ-'))
        self.assertEqual(data['data']['booking']['status'], 'CONFIRMED')

    def test_duplicate_booking_conflict_rejection(self):
        """CRITICAL: Two users attempting to book the exact same slot on the same date must return 409 Conflict."""
        booking_date = (date.today() + timedelta(days=3)).strftime('%Y-%m-%d')

        # User 1 books slot 1
        res1 = self.client.post('/api/bookings', json={
            'turf_id': self.turf.id,
            'slot_id': self.slot1.id,
            'booking_date': booking_date,
            'sport': 'Football'
        }, headers={'Authorization': f'Bearer {self.user1_token}'})
        self.assertEqual(res1.status_code, 201)

        # User 2 attempts to book the SAME slot on the SAME date
        res2 = self.client.post('/api/bookings', json={
            'turf_id': self.turf.id,
            'slot_id': self.slot1.id,
            'booking_date': booking_date,
            'sport': 'Football'
        }, headers={'Authorization': f'Bearer {self.user2_token}'})

        # MUST return HTTP 409 Conflict with BOOKING_CONFLICT
        self.assertEqual(res2.status_code, 409)
        data2 = res2.get_json()
        self.assertFalse(data2['success'])
        self.assertEqual(data2['error'], 'BOOKING_CONFLICT')

    def test_booking_cancellation_and_slot_release(self):
        """Cancelling a booking must release the slot, allowing re-booking."""
        booking_date = (date.today() + timedelta(days=4)).strftime('%Y-%m-%d')

        # 1. User 1 books slot
        res = self.client.post('/api/bookings', json={
            'turf_id': self.turf.id,
            'slot_id': self.slot2.id,
            'booking_date': booking_date,
            'sport': 'Cricket'
        }, headers={'Authorization': f'Bearer {self.user1_token}'})
        booking_id = res.get_json()['data']['booking']['id']

        # 2. User 1 cancels booking
        cancel_res = self.client.put(f'/api/bookings/{booking_id}/cancel', headers={
            'Authorization': f'Bearer {self.user1_token}'
        })
        self.assertEqual(cancel_res.status_code, 200)
        self.assertEqual(cancel_res.get_json()['data']['booking']['status'], 'CANCELLED')

        # 3. User 2 can now successfully book the released slot
        rebook_res = self.client.post('/api/bookings', json={
            'turf_id': self.turf.id,
            'slot_id': self.slot2.id,
            'booking_date': booking_date,
            'sport': 'Cricket'
        }, headers={'Authorization': f'Bearer {self.user2_token}'})
        self.assertEqual(rebook_res.status_code, 201)
        self.assertTrue(rebook_res.get_json()['success'])

    # =========================================================================
    # 4. TOURNAMENT TESTS
    # =========================================================================
    def test_tournament_listing(self):
        res = self.client.get('/api/tournaments')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(len(data['data']['tournaments']), 1)

    def test_tournament_team_registration(self):
        res = self.client.post(f'/api/tournaments/{self.tournament.id}/register', json={
            'team_name': 'Thunderbolts FC',
            'captain_name': 'Captain Alex',
            'contact': '9840112233',
            'player_count': 7,
            'players': 'Alex, Ben, Chris, Dan, Eric, Fred, George'
        }, headers={'Authorization': f'Bearer {self.user1_token}'})

        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['registration']['team_name'], 'Thunderbolts FC')

    def test_tournament_duplicate_team_rejection(self):
        # Register Team 1
        self.client.post(f'/api/tournaments/{self.tournament.id}/register', json={
            'team_name': 'Thunderbolts FC',
            'captain_name': 'Captain Alex',
            'contact': '9840112233',
            'player_count': 7
        }, headers={'Authorization': f'Bearer {self.user1_token}'})

        # Register same team name
        res = self.client.post(f'/api/tournaments/{self.tournament.id}/register', json={
            'team_name': 'Thunderbolts FC',
            'captain_name': 'Different Captain',
            'contact': '9999999999',
            'player_count': 7
        }, headers={'Authorization': f'Bearer {self.user2_token}'})

        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.get_json()['error'], 'DUPLICATE_TEAM_NAME')

    def test_tournament_capacity_limit(self):
        # Fill capacity (max_teams = 2)
        self.client.post(f'/api/tournaments/{self.tournament.id}/register', json={
            'team_name': 'Team Alpha',
            'captain_name': 'Cap A',
            'contact': '9840111111',
            'player_count': 5
        }, headers={'Authorization': f'Bearer {self.user1_token}'})

        self.client.post(f'/api/tournaments/{self.tournament.id}/register', json={
            'team_name': 'Team Beta',
            'captain_name': 'Cap B',
            'contact': '9840222222',
            'player_count': 5
        }, headers={'Authorization': f'Bearer {self.user2_token}'})

        # 3rd registration must be rejected as FULL
        res = self.client.post(f'/api/tournaments/{self.tournament.id}/register', json={
            'team_name': 'Team Gamma',
            'captain_name': 'Cap C',
            'contact': '9840333333',
            'player_count': 5
        }, headers={'Authorization': f'Bearer {self.user1_token}'})

        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.get_json()['error'], 'TOURNAMENT_FULL')

    # =========================================================================
    # 5. ADMIN STATISTICS TESTS
    # =========================================================================
    def test_admin_stats(self):
        res = self.client.get('/api/admin/stats', headers={
            'Authorization': f'Bearer {self.admin_token}'
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        stats = data['data']['stats']
        self.assertIn('total_users', stats)
        self.assertIn('total_revenue', stats)
        self.assertIn('total_turfs', stats)

    # =========================================================================
    # 6. CHATBOT (TURF-BOT) TESTS
    # =========================================================================
    def test_chatbot_football_query(self):
        res = self.client.post('/api/chatbot/message', json={
            'message': 'Find football turfs in Chennai'
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertIn('Football', data['data']['reply'])

    def test_chatbot_cheapest_query(self):
        res = self.client.post('/api/chatbot/message', json={
            'message': 'Show me the cheapest turf'
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn('affordable', data['data']['reply'].lower())


if __name__ == '__main__':
    unittest.main()
