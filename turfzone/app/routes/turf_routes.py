from datetime import date, datetime
from flask import Blueprint, request, jsonify, g
from app.models import db, Turf, TimeSlot, Booking, Review
from app.auth import admin_required, login_required

turf_bp = Blueprint('turfs', __name__, url_prefix='/api/turfs')

DEFAULT_SLOT_TIMES = [
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


@turf_bp.route('', methods=['GET'])
def get_turfs():
    search_query = request.args.get('search', '').strip().lower()
    sport_filter = request.args.get('sport', '').strip()
    location_filter = request.args.get('location', '').strip()
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    min_rating = request.args.get('min_rating', type=float)
    sort_by = request.args.get('sort', 'rating_desc')
    include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'

    query = Turf.query

    if not include_inactive:
        query = query.filter_by(is_active=True)

    if search_query:
        query = query.filter(
            db.or_(
                db.func.lower(Turf.name).contains(search_query),
                db.func.lower(Turf.location).contains(search_query),
                db.func.lower(Turf.address).contains(search_query),
                db.func.lower(Turf.sport).contains(search_query),
                db.func.lower(Turf.description).contains(search_query)
            )
        )

    if sport_filter and sport_filter.lower() != 'all':
        query = query.filter(db.func.lower(Turf.sport).contains(sport_filter.lower()))

    if location_filter and location_filter.lower() != 'all':
        query = query.filter(db.func.lower(Turf.location).contains(location_filter.lower()))

    if min_price is not None:
        query = query.filter(Turf.price_per_hour >= min_price)

    if max_price is not None:
        query = query.filter(Turf.price_per_hour <= max_price)

    if min_rating is not None:
        query = query.filter(Turf.rating >= min_rating)

    # Sorting
    if sort_by == 'price_asc':
        query = query.order_by(Turf.price_per_hour.asc())
    elif sort_by == 'price_desc':
        query = query.order_by(Turf.price_per_hour.desc())
    elif sort_by == 'rating_desc':
        query = query.order_by(Turf.rating.desc(), Turf.reviews_count.desc())
    elif sort_by == 'newest':
        query = query.order_by(Turf.created_at.desc())
    else:
        query = query.order_by(Turf.rating.desc())

    turfs = query.all()
    return jsonify({
        'success': True,
        'message': f'Found {len(turfs)} turfs',
        'data': {
            'turfs': [t.to_dict() for t in turfs],
            'count': len(turfs)
        }
    }), 200


@turf_bp.route('/<int:turf_id>', methods=['GET'])
def get_turf(turf_id):
    turf = db.session.get(Turf, turf_id)
    if not turf:
        return jsonify({
            'success': False,
            'message': f'Turf with ID {turf_id} was not found.',
            'error': 'TURF_NOT_FOUND'
        }), 404

    return jsonify({
        'success': True,
        'message': 'Turf details retrieved',
        'data': {
            'turf': turf.to_dict(include_slots=True)
        }
    }), 200


@turf_bp.route('/<int:turf_id>/slots', methods=['GET'])
def get_turf_slots(turf_id):
    turf = db.session.get(Turf, turf_id)
    if not turf:
        return jsonify({
            'success': False,
            'message': f'Turf with ID {turf_id} was not found.',
            'error': 'TURF_NOT_FOUND'
        }), 404

    slots = TimeSlot.query.filter_by(turf_id=turf_id).order_by(TimeSlot.start_time).all()
    return jsonify({
        'success': True,
        'data': {
            'slots': [s.to_dict() for s in slots]
        }
    }), 200


@turf_bp.route('/<int:turf_id>/availability', methods=['GET'])
def get_turf_availability(turf_id):
    turf = db.session.get(Turf, turf_id)
    if not turf:
        return jsonify({
            'success': False,
            'message': f'Turf with ID {turf_id} was not found.',
            'error': 'TURF_NOT_FOUND'
        }), 404

    date_str = request.args.get('date')
    if not date_str:
        return jsonify({
            'success': False,
            'message': 'Query parameter "date" (YYYY-MM-DD) is required.',
            'error': 'MISSING_DATE'
        }), 400

    try:
        query_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({
            'success': False,
            'message': 'Invalid date format. Expected YYYY-MM-DD.',
            'error': 'INVALID_DATE'
        }), 400

    today = date.today()
    is_past_date = query_date < today

    # Get slots for this turf
    slots = TimeSlot.query.filter_by(turf_id=turf_id).order_by(TimeSlot.start_time).all()

    # Get confirmed active bookings for this date and turf
    active_bookings = Booking.query.filter_by(
        turf_id=turf_id,
        booking_date=query_date,
        status='CONFIRMED'
    ).all()
    booked_slot_ids = {b.slot_id for b in active_bookings}

    slot_availability = []
    available_count = 0
    booked_count = 0

    for s in slots:
        if not turf.is_active or is_past_date:
            status = 'DISABLED'
        elif s.id in booked_slot_ids:
            status = 'BOOKED'
            booked_count += 1
        else:
            status = 'AVAILABLE'
            available_count += 1

        slot_availability.append({
            'id': s.id,
            'turf_id': s.turf_id,
            'start_time': s.start_time,
            'end_time': s.end_time,
            'formatted': f"{s.start_time} - {s.end_time}",
            'status': status
        })

    return jsonify({
        'success': True,
        'message': f'Availability retrieved for {query_date.strftime("%Y-%m-%d")}',
        'data': {
            'turf_id': turf.id,
            'turf_name': turf.name,
            'date': query_date.strftime('%Y-%m-%d'),
            'is_active': turf.is_active,
            'is_past_date': is_past_date,
            'total_slots': len(slots),
            'available_slots': available_count,
            'booked_slots': booked_count,
            'slots': slot_availability
        }
    }), 200


@turf_bp.route('', methods=['POST'])
@admin_required
def create_turf():
    data = request.get_json() or {}
    name = (data.get('name') or '').strip()
    location = (data.get('location') or '').strip()
    address = (data.get('address') or '').strip()
    sport = (data.get('sport') or '').strip()
    description = (data.get('description') or '').strip()
    facilities = (data.get('facilities') or '').strip()
    price_per_hour = data.get('price_per_hour')
    rating = data.get('rating', 4.8)
    image_url = (data.get('image_url') or '').strip()

    if not all([name, location, address, sport, description, price_per_hour]):
        return jsonify({
            'success': False,
            'message': 'Missing required turf fields: name, location, address, sport, description, price_per_hour.',
            'error': 'VALIDATION_ERROR'
        }), 400

    try:
        price = float(price_per_hour)
        if price <= 0:
            raise ValueError()
    except (ValueError, TypeError):
        return jsonify({
            'success': False,
            'message': 'Price per hour must be a positive number.',
            'error': 'INVALID_PRICE'
        }), 400

    if not image_url:
        image_url = "https://images.unsplash.com/photo-1529900245534-47fbf8221565?auto=format&fit=crop&w=1200&q=80"

    turf = Turf(
        name=name,
        location=location,
        address=address,
        sport=sport,
        description=description,
        facilities=facilities or "Floodlights, Parking, Drinking Water",
        price_per_hour=price,
        rating=float(rating) if rating else 4.8,
        reviews_count=0,
        image_url=image_url,
        is_active=True
    )
    db.session.add(turf)
    db.session.commit()

    # Automatically create default time slots for the new turf
    for start_t, end_t in DEFAULT_SLOT_TIMES:
        slot = TimeSlot(
            turf_id=turf.id,
            start_time=start_t,
            end_time=end_t
        )
        db.session.add(slot)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'Turf "{turf.name}" created successfully with time slots.',
        'data': {
            'turf': turf.to_dict(include_slots=True)
        }
    }), 201


@turf_bp.route('/<int:turf_id>', methods=['PUT'])
@admin_required
def update_turf(turf_id):
    turf = db.session.get(Turf, turf_id)
    if not turf:
        return jsonify({
            'success': False,
            'message': f'Turf with ID {turf_id} was not found.',
            'error': 'TURF_NOT_FOUND'
        }), 404

    data = request.get_json() or {}
    if 'name' in data:
        turf.name = data['name'].strip()
    if 'location' in data:
        turf.location = data['location'].strip()
    if 'address' in data:
        turf.address = data['address'].strip()
    if 'sport' in data:
        turf.sport = data['sport'].strip()
    if 'description' in data:
        turf.description = data['description'].strip()
    if 'facilities' in data:
        turf.facilities = data['facilities'].strip()
    if 'price_per_hour' in data:
        try:
            turf.price_per_hour = float(data['price_per_hour'])
        except (ValueError, TypeError):
            return jsonify({'success': False, 'message': 'Invalid price per hour.', 'error': 'INVALID_PRICE'}), 400
    if 'rating' in data:
        try:
            turf.rating = float(data['rating'])
        except (ValueError, TypeError):
            pass
    if 'image_url' in data:
        turf.image_url = data['image_url'].strip()
    if 'is_active' in data:
        turf.is_active = bool(data['is_active'])

    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'Turf "{turf.name}" updated successfully.',
        'data': {
            'turf': turf.to_dict(include_slots=True)
        }
    }), 200


@turf_bp.route('/<int:turf_id>', methods=['DELETE'])
@admin_required
def delete_turf(turf_id):
    turf = db.session.get(Turf, turf_id)
    if not turf:
        return jsonify({
            'success': False,
            'message': f'Turf with ID {turf_id} was not found.',
            'error': 'TURF_NOT_FOUND'
        }), 404

    # Check for upcoming active bookings
    active_bookings = Booking.query.filter_by(turf_id=turf_id, status='CONFIRMED').first()
    if active_bookings:
        # Instead of deleting, deactivate
        turf.is_active = False
        db.session.commit()
        return jsonify({
            'success': True,
            'message': f'Turf "{turf.name}" has active bookings, so it was deactivated instead of deleted.',
            'data': {'turf': turf.to_dict()}
        }), 200

    db.session.delete(turf)
    db.session.commit()
    return jsonify({
        'success': True,
        'message': f'Turf "{turf.name}" was permanently deleted.'
    }), 200


@turf_bp.route('/<int:turf_id>/reviews', methods=['GET'])
def get_turf_reviews(turf_id):
    turf = db.session.get(Turf, turf_id)
    if not turf:
        return jsonify({'success': False, 'message': 'Turf not found', 'error': 'TURF_NOT_FOUND'}), 404

    reviews = Review.query.filter_by(turf_id=turf_id).order_by(Review.created_at.desc()).all()
    return jsonify({
        'success': True,
        'data': {
            'reviews': [r.to_dict() for r in reviews],
            'count': len(reviews),
            'rating': round(turf.rating, 1)
        }
    }), 200


@turf_bp.route('/<int:turf_id>/reviews', methods=['POST'])
@login_required
def add_turf_review(turf_id):
    turf = db.session.get(Turf, turf_id)
    if not turf:
        return jsonify({'success': False, 'message': 'Turf not found', 'error': 'TURF_NOT_FOUND'}), 404

    data = request.get_json() or {}
    rating_val = data.get('rating')
    comment = (data.get('comment') or '').strip()

    if not rating_val or not comment:
        return jsonify({'success': False, 'message': 'Rating (1-5) and comment are required.', 'error': 'VALIDATION_ERROR'}), 400

    try:
        rating_int = int(rating_val)
        if rating_int < 1 or rating_int > 5:
            raise ValueError()
    except (ValueError, TypeError):
        return jsonify({'success': False, 'message': 'Rating must be an integer between 1 and 5.', 'error': 'INVALID_RATING'}), 400

    review = Review(
        turf_id=turf.id,
        user_id=g.current_user.id,
        rating=rating_int,
        comment=comment
    )
    db.session.add(review)
    db.session.commit()

    # Recalculate average rating & reviews count
    all_reviews = Review.query.filter_by(turf_id=turf.id).all()
    if all_reviews:
        turf.rating = sum(r.rating for r in all_reviews) / len(all_reviews)
        turf.reviews_count = len(all_reviews)
        db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Review submitted successfully!',
        'data': {
            'review': review.to_dict(),
            'turf_rating': round(turf.rating, 1),
            'reviews_count': turf.reviews_count
        }
    }), 201

