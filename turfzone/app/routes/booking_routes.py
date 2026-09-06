import random
from datetime import date, datetime
from flask import Blueprint, request, jsonify, g
from app.models import db, Booking, Turf, TimeSlot
from app.auth import login_required

booking_bp = Blueprint('bookings', __name__, url_prefix='/api/bookings')


def generate_booking_reference():
    year = datetime.now().year
    # Unique reference generation
    while True:
        seq = random.randint(10000, 99999)
        ref = f"TZ-{year}-{seq}"
        if not Booking.query.filter_by(booking_reference=ref).first():
            return ref


@booking_bp.route('', methods=['POST'])
@login_required
def create_booking():
    data = request.get_json() or {}
    turf_id = data.get('turf_id')
    slot_id = data.get('slot_id')
    date_str = data.get('booking_date')
    sport = (data.get('sport') or '').strip()

    # 1. Input validation
    if not turf_id or not slot_id or not date_str:
        return jsonify({
            'success': False,
            'message': 'turf_id, slot_id, and booking_date (YYYY-MM-DD) are required.',
            'error': 'VALIDATION_ERROR'
        }), 400

    # 2. Validate Turf
    turf = db.session.get(Turf, turf_id)
    if not turf:
        return jsonify({
            'success': False,
            'message': 'Selected turf does not exist.',
            'error': 'TURF_NOT_FOUND'
        }), 404

    if not turf.is_active:
        return jsonify({
            'success': False,
            'message': 'This turf is currently inactive and cannot be booked.',
            'error': 'TURF_INACTIVE'
        }), 400

    # 3. Validate Date
    try:
        booking_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({
            'success': False,
            'message': 'Invalid date format. Expected YYYY-MM-DD.',
            'error': 'INVALID_DATE'
        }), 400

    today = date.today()
    if booking_date < today:
        return jsonify({
            'success': False,
            'message': 'Cannot book slots for past dates.',
            'error': 'PAST_DATE'
        }), 400

    # 4. Validate Slot
    slot = db.session.get(TimeSlot, slot_id)
    if not slot:
        return jsonify({
            'success': False,
            'message': 'Selected time slot does not exist.',
            'error': 'SLOT_NOT_FOUND'
        }), 404

    if slot.turf_id != turf.id:
        return jsonify({
            'success': False,
            'message': 'The selected time slot does not belong to this turf.',
            'error': 'INVALID_SLOT_FOR_TURF'
        }), 400

    # 5. Check Concurrency Conflict (Atomic check)
    existing_booking = Booking.query.filter_by(
        turf_id=turf.id,
        slot_id=slot.id,
        booking_date=booking_date,
        status='CONFIRMED'
    ).first()

    if existing_booking:
        return jsonify({
            'success': False,
            'message': 'This slot has already been booked. Please select another slot.',
            'error': 'BOOKING_CONFLICT'
        }), 409

    # 6. Create Booking with Optional Equipment Add-ons
    ref = generate_booking_reference()
    selected_sport = sport or (turf.sport.split(',')[0].strip() if turf.sport else 'Football')
    addons_data = data.get('addons') or []
    
    total_price = turf.price_per_hour
    addons_str = ""

    if isinstance(addons_data, list) and addons_data:
        addons_str = ", ".join([str(a).strip() for a in addons_data if str(a).strip()])
        # Calculate addon pricing
        for a in addons_data:
            a_lower = str(a).lower()
            if 'football' in a_lower or 'ball' in a_lower:
                total_price += 100.0
            elif 'bibs' in a_lower or 'vest' in a_lower:
                total_price += 150.0
            elif 'referee' in a_lower:
                total_price += 350.0
            elif 'hydration' in a_lower or 'energy' in a_lower or 'drink' in a_lower:
                total_price += 200.0

    booking = Booking(
        booking_reference=ref,
        user_id=g.current_user.id,
        turf_id=turf.id,
        slot_id=slot.id,
        booking_date=booking_date,
        sport=selected_sport,
        price=total_price,
        addons=addons_str if addons_str else None,
        status='CONFIRMED'
    )

    try:
        db.session.add(booking)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'A conflict occurred while creating your booking. Please try again.',
            'error': 'BOOKING_CONFLICT'
        }), 409

    return jsonify({
        'success': True,
        'message': 'Booking confirmed successfully!',
        'data': {
            'booking': booking.to_dict()
        }
    }), 201


@booking_bp.route('', methods=['GET'])
@login_required
def get_bookings():
    user = g.current_user
    filter_type = request.args.get('tab', 'all').lower()  # upcoming, current, previous, all
    today = date.today()

    query = Booking.query

    # Regular users can only see their own bookings
    if user.role != 'ADMIN' or request.args.get('my_only', 'false').lower() == 'true':
        query = query.filter_by(user_id=user.id)

    if filter_type == 'upcoming':
        query = query.filter(
            Booking.status == 'CONFIRMED',
            Booking.booking_date > today
        )
    elif filter_type == 'current':
        query = query.filter(
            Booking.status == 'CONFIRMED',
            Booking.booking_date == today
        )
    elif filter_type == 'previous':
        query = query.filter(
            db.or_(
                Booking.status.in_(['CANCELLED', 'COMPLETED']),
                db.and_(Booking.status == 'CONFIRMED', Booking.booking_date < today)
            )
        )

    bookings = query.order_by(Booking.booking_date.desc(), Booking.created_at.desc()).all()

    # Automatically mark past confirmed bookings as COMPLETED on display
    modified = False
    for b in bookings:
        if b.status == 'CONFIRMED' and b.booking_date < today:
            b.status = 'COMPLETED'
            modified = True
    if modified:
        db.session.commit()

    return jsonify({
        'success': True,
        'message': f'Retrieved {len(bookings)} bookings',
        'data': {
            'bookings': [b.to_dict() for b in bookings],
            'count': len(bookings)
        }
    }), 200


@booking_bp.route('/<int:booking_id>', methods=['GET'])
@login_required
def get_booking(booking_id):
    booking = db.session.get(Booking, booking_id)
    if not booking:
        return jsonify({
            'success': False,
            'message': f'Booking with ID {booking_id} was not found.',
            'error': 'BOOKING_NOT_FOUND'
        }), 404

    # Access check
    if g.current_user.role != 'ADMIN' and booking.user_id != g.current_user.id:
        return jsonify({
            'success': False,
            'message': 'You are not authorized to view this booking.',
            'error': 'FORBIDDEN'
        }), 403

    return jsonify({
        'success': True,
        'data': {
            'booking': booking.to_dict()
        }
    }), 200


@booking_bp.route('/<int:booking_id>/cancel', methods=['PUT'])
@login_required
def cancel_booking(booking_id):
    booking = db.session.get(Booking, booking_id)
    if not booking:
        return jsonify({
            'success': False,
            'message': f'Booking with ID {booking_id} was not found.',
            'error': 'BOOKING_NOT_FOUND'
        }), 404

    # Access check
    if g.current_user.role != 'ADMIN' and booking.user_id != g.current_user.id:
        return jsonify({
            'success': False,
            'message': 'You are not authorized to cancel this booking.',
            'error': 'FORBIDDEN'
        }), 403

    if booking.status == 'CANCELLED':
        return jsonify({
            'success': False,
            'message': 'This booking is already cancelled.',
            'error': 'ALREADY_CANCELLED'
        }), 400

    if booking.status == 'COMPLETED':
        return jsonify({
            'success': False,
            'message': 'Cannot cancel a completed booking.',
            'error': 'CANNOT_CANCEL_COMPLETED'
        }), 400

    booking.status = 'CANCELLED'
    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'Booking {booking.booking_reference} has been successfully cancelled. The slot is now available.',
        'data': {
            'booking': booking.to_dict()
        }
    }), 200
