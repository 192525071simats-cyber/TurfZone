from datetime import date, datetime, timedelta
from app.models import db, User, Turf, TimeSlot, Booking, Tournament, TournamentRegistration, Review


def seed_database():
    """Seeds the database with initial realistic data if empty."""
    if User.query.first() is not None:
        return  # Database already seeded

    print("Seeding database with realistic TurfZone data...")

    # 1. Users
    admin = User(
        name="TurfZone Admin",
        email="admin@turfzone.com",
        phone="+91 9876543210",
        role="ADMIN",
        is_active=True
    )
    admin.set_password("Admin@123")

    user1 = User(
        name="Dhanesh Kumar",
        email="user@turfzone.com",
        phone="+91 9840123456",
        role="USER",
        is_active=True
    )
    user1.set_password("User@123")

    user2 = User(
        name="Rahul Sharma",
        email="rahul@turfzone.com",
        phone="+91 9962001122",
        role="USER",
        is_active=True
    )
    user2.set_password("User@123")

    db.session.add_all([admin, user1, user2])
    db.session.commit()

    # 2. Turfs
    turfs_data = [
        {
            "name": "Marina Champions Arena",
            "location": "Triplicane, Chennai",
            "address": "45 Marina Beach Expressway, Near Light House, Triplicane, Chennai 600005",
            "sport": "Football, Cricket",
            "description": "Premium FIFA-standard synthetic turf located right by the Marina coastline. Features 4K high-mast floodlights, ultra-cushioned shock pad sub-base for knee protection, and viewing gallery for 100+ spectators.",
            "facilities": "Floodlights, Parking, Changing Rooms, Washrooms, Drinking Water, Equipment Rental, Cafeteria, Spectator Seating",
            "price_per_hour": 1200.0,
            "rating": 4.9,
            "reviews_count": 86,
            "image_url": "https://images.unsplash.com/photo-1529900245534-47fbf8221565?auto=format&fit=crop&w=1200&q=80",
            "is_active": True
        },
        {
            "name": "Velachery Super Turf Hub",
            "location": "Velachery, Chennai",
            "address": "12 100 Feet Bypass Road, Near Phoenix Marketcity, Velachery, Chennai 600042",
            "sport": "Football, Cricket, Badminton",
            "description": "Chennai's premier multi-sport arena featuring 2 international 7-a-side football grounds and 3 high-speed box cricket pitches with automated bowling machine capability.",
            "facilities": "Floodlights, Parking, Changing Rooms, Washrooms, Drinking Water, Equipment Rental, Bowling Machine, Lockers",
            "price_per_hour": 1000.0,
            "rating": 4.8,
            "reviews_count": 124,
            "image_url": "https://images.unsplash.com/photo-1551958219-acbc608c6377?auto=format&fit=crop&w=1200&q=80",
            "is_active": True
        },
        {
            "name": "ECR Coastal Kickoff Ground",
            "location": "Injambakkam, Chennai",
            "address": "88 East Coast Road, Near VGP Golden Beach, Injambakkam, Chennai 600115",
            "sport": "Football, Cricket",
            "description": "Scenic beachfront sports facility offering fresh ocean breeze, tournament-grade Monofilament turf, post-match chill lounge, and live match recording setup.",
            "facilities": "Floodlights, Free Parking, Washrooms, Drinking Water, Equipment Rental, Lounge, Match Video Recording",
            "price_per_hour": 1400.0,
            "rating": 4.9,
            "reviews_count": 62,
            "image_url": "https://images.unsplash.com/photo-1508098682722-e99c43a406b2?auto=format&fit=crop&w=1200&q=80",
            "is_active": True
        },
        {
            "name": "Anna Nagar Smashers & Strikers",
            "location": "Anna Nagar, Chennai",
            "address": "24 2nd Avenue, Near Roundtana, Anna Nagar East, Chennai 600102",
            "sport": "Football, Basketball, Tennis",
            "description": "Centrally located multi-sport complex equipped with ITF approved synthetic tennis/basketball court and 5v5 turf. Certified coaching and referee services available on booking.",
            "facilities": "Floodlights, Parking, Changing Rooms, Washrooms, Drinking Water, Equipment Rental, Shower Stalls, Referee On Request",
            "price_per_hour": 1500.0,
            "rating": 4.9,
            "reviews_count": 94,
            "image_url": "https://images.unsplash.com/photo-1574629810360-7efbbe195018?auto=format&fit=crop&w=1200&q=80",
            "is_active": True
        },
        {
            "name": "OMR High-Octane Turf Club",
            "location": "Sholinganallur, Chennai",
            "address": "Plot 5B OMR IT Expressway, Sholinganallur Junction, Chennai 600119",
            "sport": "Football, Cricket, Badminton",
            "description": "The favorite night-hub for corporate leagues and weekend tournaments. Dual box cricket nets with speed guns, seamless LED floodlighting, and dedicated corporate team packages.",
            "facilities": "Floodlights, Parking, Changing Rooms, Washrooms, Drinking Water, Equipment Rental, Speed Gun, Corporate Lounge",
            "price_per_hour": 900.0,
            "rating": 4.7,
            "reviews_count": 148,
            "image_url": "https://images.unsplash.com/photo-1518604667503-4658424bb6cc?auto=format&fit=crop&w=1200&q=80",
            "is_active": True
        },
        {
            "name": "T. Nagar Box Arena",
            "location": "T. Nagar, Chennai",
            "address": "33 Venkatanarayana Road, Near Panagal Park, T. Nagar, Chennai 600017",
            "sport": "Cricket, Football",
            "description": "High-intensity enclosed box cricket & futsal arena in the vibrant core of Chennai. Includes professional leather and tennis ball bowling machines, scoreboard display, and sound system.",
            "facilities": "Floodlights, Washrooms, Drinking Water, Equipment Rental, Bowling Machine, Digital Scoreboard",
            "price_per_hour": 1100.0,
            "rating": 4.8,
            "reviews_count": 78,
            "image_url": "https://images.unsplash.com/photo-1534438327276-14e5300c3a48?auto=format&fit=crop&w=1200&q=80",
            "is_active": True
        }
    ]

    turf_objects = []
    for td in turfs_data:
        turf = Turf(**td)
        db.session.add(turf)
        turf_objects.append(turf)

    db.session.commit()

    # 3. Time Slots for each turf
    slot_times = [
        ("06:00", "07:00"),
        ("07:00", "08:00"),
        ("08:00", "09:00"),
        ("09:00", "10:00"),
        ("10:00", "11:00"),
        ("11:00", "12:00"),
        ("14:00", "15:00"),
        ("15:00", "16:00"),
        ("16:00", "17:00"),
        ("17:00", "18:00"),
        ("18:00", "19:00"),
        ("19:00", "20:00"),
        ("20:00", "21:00"),
        ("21:00", "22:00")
    ]

    all_slots = []
    for turf in turf_objects:
        for start_t, end_t in slot_times:
            slot = TimeSlot(
                turf_id=turf.id,
                start_time=start_t,
                end_time=end_t
            )
            db.session.add(slot)
            all_slots.append(slot)

    db.session.commit()

    # 4. Tournaments
    today = date.today()
    tournaments_data = [
        {
            "name": "Chennai Premier Turf League 2026",
            "sport": "Football",
            "description": "The biggest 7v7 knockout football championship in Chennai. 16 elite teams battling across 2 exciting weekends for ₹50,000 cash prize and gold championship trophy.",
            "venue": "Marina Champions Arena",
            "tournament_date": today + timedelta(days=20),
            "registration_deadline": today + timedelta(days=15),
            "entry_fee": 3000.0,
            "max_teams": 16,
            "status": "OPEN",
            "image_url": "https://images.unsplash.com/photo-1579952363873-27f3bade9f55?auto=format&fit=crop&w=800&q=80"
        },
        {
            "name": "Midnight Box Cricket Clash",
            "sport": "Cricket",
            "description": "High-octane night tournament under LED floodlights. 6-overs a side, powerplay overs, player of the match cash bonuses, and DJ entertainment.",
            "venue": "T. Nagar Box Arena",
            "tournament_date": today + timedelta(days=12),
            "registration_deadline": today + timedelta(days=8),
            "entry_fee": 2500.0,
            "max_teams": 12,
            "status": "OPEN",
            "image_url": "https://images.unsplash.com/photo-1531415074868-036b1c57e3b0?auto=format&fit=crop&w=800&q=80"
        },
        {
            "name": "ECR Coastal 5v5 Strikers Cup",
            "sport": "Football",
            "description": "Fast-paced beachside football tournament. 8 team round-robin into knockout playoffs with live YouTube streaming.",
            "venue": "ECR Coastal Kickoff Ground",
            "tournament_date": today + timedelta(days=5),
            "registration_deadline": today + timedelta(days=2),
            "entry_fee": 3500.0,
            "max_teams": 8,
            "status": "FULL",
            "image_url": "https://images.unsplash.com/photo-1526232761682-d26e03ac148e?auto=format&fit=crop&w=800&q=80"
        },
        {
            "name": "Anna Nagar All-Star Tennis Open",
            "sport": "Tennis",
            "description": "Men's & Women's open doubles tennis tournament. Synthetic hardcourt surface, certified ball-boys, and official ranking points.",
            "venue": "Anna Nagar Smashers & Strikers",
            "tournament_date": today + timedelta(days=28),
            "registration_deadline": today + timedelta(days=22),
            "entry_fee": 2000.0,
            "max_teams": 16,
            "status": "OPEN",
            "image_url": "https://images.unsplash.com/photo-1595435934249-5df7ed86e1c0?auto=format&fit=crop&w=800&q=80"
        },
        {
            "name": "OMR Corporate Smashers Championship",
            "sport": "Badminton",
            "description": "Corporate badminton tournament open to all IT/Tech & enterprise teams across OMR corridor. Singles and Doubles categories.",
            "venue": "OMR High-Octane Turf Club",
            "tournament_date": today + timedelta(days=25),
            "registration_deadline": today + timedelta(days=19),
            "entry_fee": 1800.0,
            "max_teams": 20,
            "status": "OPEN",
            "image_url": "https://images.unsplash.com/photo-1626224583764-f87db24ac4ea?auto=format&fit=crop&w=800&q=80"
        }
    ]

    tournament_objects = []
    for td in tournaments_data:
        tourn = Tournament(**td)
        db.session.add(tourn)
        tournament_objects.append(tourn)

    db.session.commit()

    # 5. Tournament Registrations for Demo
    # Populate ECR Cup to FULL (8 teams)
    ecr_tourn = tournament_objects[2]
    team_names = ["Coastal Thunder", "Marina Wolves", "ECR Strikers", "Bay City FC", "Chennai United", "Velachery Hawks", "OMR Ninjas", "Red Dragon FC"]
    for i, tname in enumerate(team_names):
        reg = TournamentRegistration(
            tournament_id=ecr_tourn.id,
            user_id=user1.id if i == 0 else user2.id,
            team_name=tname,
            captain_name=f"Captain {tname.split()[0]}",
            contact=f"+91 98401122{i:02d}",
            player_count=7,
            players=f"Player 1, Player 2, Player 3, Player 4, Player 5, Player 6, Player 7",
            registration_reference=f"TR-2026-{1000 + i}"
        )
        db.session.add(reg)

    # Populate Chennai Premier (5 teams)
    cptl_tourn = tournament_objects[0]
    cptl_teams = ["Chennai Kings FC", "Anna Nagar Strikers", "Triplicane Shooters", "Madras FC", "Southern Stars"]
    for i, tname in enumerate(cptl_teams):
        reg = TournamentRegistration(
            tournament_id=cptl_tourn.id,
            user_id=user2.id,
            team_name=tname,
            captain_name=f"Captain {tname.split()[0]}",
            contact=f"+91 97890011{i:02d}",
            player_count=8,
            players=f"Player A, Player B, Player C, Player D, Player E, Player F, Player G, Player H",
            registration_reference=f"TR-2026-{2000 + i}"
        )
        db.session.add(reg)

    db.session.commit()

    # 6. Sample Initial Bookings for Demo User
    turf1 = turf_objects[0]  # Marina Arena
    turf2 = turf_objects[1]  # Velachery Super Turf
    turf3 = turf_objects[3]  # Anna Nagar

    slot_18_19_t1 = TimeSlot.query.filter_by(turf_id=turf1.id, start_time="18:00").first()
    slot_19_20_t1 = TimeSlot.query.filter_by(turf_id=turf1.id, start_time="19:00").first()
    slot_07_08_t2 = TimeSlot.query.filter_by(turf_id=turf2.id, start_time="07:00").first()
    slot_20_21_t3 = TimeSlot.query.filter_by(turf_id=turf3.id, start_time="20:00").first()

    # Booking 1: Upcoming tomorrow
    b1 = Booking(
        booking_reference="TZ-2026-00001",
        user_id=user1.id,
        turf_id=turf1.id,
        slot_id=slot_18_19_t1.id,
        booking_date=today + timedelta(days=1),
        sport="Football",
        price=turf1.price_per_hour,
        status="CONFIRMED"
    )

    # Booking 2: Upcoming in 3 days
    b2 = Booking(
        booking_reference="TZ-2026-00002",
        user_id=user1.id,
        turf_id=turf2.id,
        slot_id=slot_07_08_t2.id,
        booking_date=today + timedelta(days=3),
        sport="Cricket",
        price=turf2.price_per_hour,
        status="CONFIRMED"
    )

    # Booking 3: Past completed booking
    b3 = Booking(
        booking_reference="TZ-2026-00003",
        user_id=user1.id,
        turf_id=turf3.id,
        slot_id=slot_20_21_t3.id,
        booking_date=today - timedelta(days=4),
        sport="Football",
        price=turf3.price_per_hour,
        status="COMPLETED"
    )

    # Booking 4: Another user's booking for conflict testing demo
    b4 = Booking(
        booking_reference="TZ-2026-00004",
        user_id=user2.id,
        turf_id=turf1.id,
        slot_id=slot_19_20_t1.id,
        booking_date=today,
        sport="Football",
        price=turf1.price_per_hour,
        status="CONFIRMED"
    )

    db.session.add_all([b1, b2, b3, b4])
    db.session.commit()

    # 7. Initial Verified Player Reviews
    rev1 = Review(
        turf_id=turf1.id,
        user_id=user1.id,
        rating=5,
        comment="Absolutely top-tier turf! The shock-absorbing grass is easy on the knees, and the floodlights are great for late night 8v8 games."
    )
    rev2 = Review(
        turf_id=turf1.id,
        user_id=user2.id,
        rating=5,
        comment="The coastal breeze makes playing football here an incredible experience. Clean locker rooms and ample parking space."
    )
    rev3 = Review(
        turf_id=turf2.id,
        user_id=user1.id,
        rating=5,
        comment="Best box cricket pitch in Velachery! Bowling machine speed is accurate and netting is super high."
    )
    db.session.add_all([rev1, rev2, rev3])
    db.session.commit()

    print("Demo database successfully initialized with reviews!")
