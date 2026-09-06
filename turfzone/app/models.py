from datetime import datetime, date, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def utc_now():
    return datetime.now(timezone.utc)


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, index=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='USER', nullable=False)  # 'USER' or 'ADMIN'
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    bookings = db.relationship('Booking', backref='user', lazy=True, cascade='all, delete-orphan')
    tournament_registrations = db.relationship('TournamentRegistration', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }


class Turf(db.Model):
    __tablename__ = 'turfs'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    sport = db.Column(db.String(100), nullable=False)  # e.g., "Football, Cricket"
    description = db.Column(db.Text, nullable=False)
    facilities = db.Column(db.Text, nullable=False)  # Comma-separated
    price_per_hour = db.Column(db.Float, nullable=False)
    rating = db.Column(db.Float, default=4.8, nullable=False)
    reviews_count = db.Column(db.Integer, default=24, nullable=False)
    image_url = db.Column(db.String(500), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    slots = db.relationship('TimeSlot', backref='turf', lazy=True, cascade='all, delete-orphan', order_by='TimeSlot.start_time')
    bookings = db.relationship('Booking', backref='turf', lazy=True, cascade='all, delete-orphan')
    reviews = db.relationship('Review', backref='turf', lazy=True, cascade='all, delete-orphan', order_by='Review.created_at.desc()')

    def to_dict(self, include_slots=False):
        data = {
            'id': self.id,
            'name': self.name,
            'location': self.location,
            'address': self.address,
            'sport': self.sport,
            'description': self.description,
            'facilities': [f.strip() for f in self.facilities.split(',') if f.strip()],
            'price_per_hour': self.price_per_hour,
            'rating': round(self.rating, 1),
            'reviews_count': self.reviews_count,
            'image_url': self.image_url,
            'is_active': self.is_active,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }
        if include_slots:
            data['slots'] = [s.to_dict() for s in self.slots]
        return data


class Review(db.Model):
    __tablename__ = 'reviews'

    id = db.Column(db.Integer, primary_key=True)
    turf_id = db.Column(db.Integer, db.ForeignKey('turfs.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    rating = db.Column(db.Integer, nullable=False)  # 1 to 5
    comment = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    user = db.relationship('User', backref='reviews')

    def to_dict(self):
        return {
            'id': self.id,
            'turf_id': self.turf_id,
            'user_id': self.user_id,
            'user_name': self.user.name if self.user else 'Verified Player',
            'rating': self.rating,
            'comment': self.comment,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }


class TimeSlot(db.Model):
    __tablename__ = 'time_slots'

    id = db.Column(db.Integer, primary_key=True)
    turf_id = db.Column(db.Integer, db.ForeignKey('turfs.id'), nullable=False, index=True)
    start_time = db.Column(db.String(10), nullable=False)  # e.g. "09:00"
    end_time = db.Column(db.String(10), nullable=False)    # e.g. "10:00"

    bookings = db.relationship('Booking', backref='slot', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'turf_id': self.turf_id,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'formatted': f"{self.start_time} - {self.end_time}"
        }


class Booking(db.Model):
    __tablename__ = 'bookings'

    id = db.Column(db.Integer, primary_key=True)
    booking_reference = db.Column(db.String(30), unique=True, index=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    turf_id = db.Column(db.Integer, db.ForeignKey('turfs.id'), nullable=False, index=True)
    slot_id = db.Column(db.Integer, db.ForeignKey('time_slots.id'), nullable=False, index=True)
    booking_date = db.Column(db.Date, nullable=False, index=True)
    sport = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    addons = db.Column(db.Text, nullable=True)  # Comma-separated list of extras
    status = db.Column(db.String(20), default='CONFIRMED', nullable=False)  # 'CONFIRMED', 'CANCELLED', 'COMPLETED'
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    __table_args__ = (
        db.Index('idx_turf_slot_date', 'turf_id', 'slot_id', 'booking_date'),
    )

    def to_dict(self):
        addons_list = [a.strip() for a in self.addons.split(',') if a.strip()] if self.addons else []
        return {
            'id': self.id,
            'booking_reference': self.booking_reference,
            'user_id': self.user_id,
            'user_name': self.user.name if self.user else None,
            'user_email': self.user.email if self.user else None,
            'user_phone': self.user.phone if self.user else None,
            'turf_id': self.turf_id,
            'turf_name': self.turf.name if self.turf else None,
            'turf_location': self.turf.location if self.turf else None,
            'turf_address': self.turf.address if self.turf else None,
            'turf_image': self.turf.image_url if self.turf else None,
            'slot_id': self.slot_id,
            'slot_time': f"{self.slot.start_time} - {self.slot.end_time}" if self.slot else None,
            'booking_date': self.booking_date.strftime('%Y-%m-%d') if self.booking_date else None,
            'sport': self.sport,
            'price': self.price,
            'addons': addons_list,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }


class Tournament(db.Model):
    __tablename__ = 'tournaments'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    sport = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    venue = db.Column(db.String(150), nullable=False)
    tournament_date = db.Column(db.Date, nullable=False)
    registration_deadline = db.Column(db.Date, nullable=False)
    entry_fee = db.Column(db.Float, nullable=False)
    max_teams = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='OPEN', nullable=False)  # 'OPEN', 'FULL', 'CLOSED', 'COMPLETED'
    image_url = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    registrations = db.relationship('TournamentRegistration', backref='tournament', lazy=True, cascade='all, delete-orphan')

    def get_dynamic_status(self):
        today = date.today()
        reg_count = len(self.registrations)
        if self.status == 'COMPLETED':
            return 'COMPLETED'
        if today > self.tournament_date:
            return 'COMPLETED'
        if today > self.registration_deadline:
            return 'CLOSED'
        if reg_count >= self.max_teams:
            return 'FULL'
        return self.status

    def to_dict(self):
        dyn_status = self.get_dynamic_status()
        reg_count = len(self.registrations)
        return {
            'id': self.id,
            'name': self.name,
            'sport': self.sport,
            'description': self.description,
            'venue': self.venue,
            'tournament_date': self.tournament_date.strftime('%Y-%m-%d') if self.tournament_date else None,
            'registration_deadline': self.registration_deadline.strftime('%Y-%m-%d') if self.registration_deadline else None,
            'entry_fee': self.entry_fee,
            'max_teams': self.max_teams,
            'registered_teams': reg_count,
            'remaining_slots': max(0, self.max_teams - reg_count),
            'status': dyn_status,
            'image_url': self.image_url,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }


class TournamentRegistration(db.Model):
    __tablename__ = 'tournament_registrations'

    id = db.Column(db.Integer, primary_key=True)
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournaments.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    team_name = db.Column(db.String(100), nullable=False)
    captain_name = db.Column(db.String(100), nullable=False)
    contact = db.Column(db.String(20), nullable=False)
    player_count = db.Column(db.Integer, nullable=False)
    players = db.Column(db.Text, nullable=True)  # Comma-separated or JSON list
    registration_reference = db.Column(db.String(30), unique=True, index=True, nullable=False)
    registration_date = db.Column(db.DateTime, default=utc_now, nullable=False)

    def to_dict(self):
        player_list = [p.strip() for p in self.players.split(',') if p.strip()] if self.players else []
        return {
            'id': self.id,
            'tournament_id': self.tournament_id,
            'tournament_name': self.tournament.name if self.tournament else None,
            'tournament_sport': self.tournament.sport if self.tournament else None,
            'tournament_date': self.tournament.tournament_date.strftime('%Y-%m-%d') if self.tournament and self.tournament.tournament_date else None,
            'venue': self.tournament.venue if self.tournament else None,
            'user_id': self.user_id,
            'team_name': self.team_name,
            'captain_name': self.captain_name,
            'contact': self.contact,
            'player_count': self.player_count,
            'players': player_list,
            'registration_reference': self.registration_reference,
            'registration_date': self.registration_date.strftime('%Y-%m-%d %H:%M:%S') if self.registration_date else None
        }
