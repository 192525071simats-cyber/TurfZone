import random
from datetime import date, datetime
from flask import Blueprint, request, jsonify, g
from app.models import db, Tournament, TournamentRegistration
from app.auth import login_required, admin_required, get_current_user

tournament_bp = Blueprint('tournaments', __name__, url_prefix='/api/tournaments')


def generate_registration_reference():
    year = datetime.now().year
    while True:
        seq = random.randint(1000, 9999)
        ref = f"TR-{year}-{seq}"
        if not TournamentRegistration.query.filter_by(registration_reference=ref).first():
            return ref


@tournament_bp.route('', methods=['GET'])
def get_tournaments():
    sport_filter = request.args.get('sport', '').strip()
    status_filter = request.args.get('status', '').strip().upper()

    query = Tournament.query

    if sport_filter and sport_filter.lower() != 'all':
        query = query.filter(db.func.lower(Tournament.sport) == sport_filter.lower())

    tournaments = query.order_by(Tournament.tournament_date.asc()).all()
    results = [t.to_dict() for t in tournaments]

    if status_filter and status_filter != 'ALL':
        results = [t for t in results if t['status'] == status_filter]

    return jsonify({
        'success': True,
        'message': f'Found {len(results)} tournaments',
        'data': {
            'tournaments': results,
            'count': len(results)
        }
    }), 200


@tournament_bp.route('/<int:tournament_id>', methods=['GET'])
def get_tournament(tournament_id):
    tourn = db.session.get(Tournament, tournament_id)
    if not tourn:
        return jsonify({
            'success': False,
            'message': f'Tournament with ID {tournament_id} was not found.',
            'error': 'TOURNAMENT_NOT_FOUND'
        }), 404

    data = tourn.to_dict()
    data['registrations'] = [r.to_dict() for r in tourn.registrations]

    return jsonify({
        'success': True,
        'data': {
            'tournament': data
        }
    }), 200


@tournament_bp.route('/<int:tournament_id>/register', methods=['POST'])
@login_required
def register_team(tournament_id):
    tourn = db.session.get(Tournament, tournament_id)
    if not tourn:
        return jsonify({
            'success': False,
            'message': f'Tournament with ID {tournament_id} was not found.',
            'error': 'TOURNAMENT_NOT_FOUND'
        }), 404

    current_status = tourn.get_dynamic_status()
    if current_status == 'FULL':
        return jsonify({
            'success': False,
            'message': 'Registration closed. This tournament has already reached its maximum team capacity.',
            'error': 'TOURNAMENT_FULL'
        }), 400

    if current_status == 'CLOSED':
        return jsonify({
            'success': False,
            'message': 'Registration deadline for this tournament has already passed.',
            'error': 'REGISTRATION_DEADLINE_PASSED'
        }), 400

    if current_status == 'COMPLETED':
        return jsonify({
            'success': False,
            'message': 'This tournament has already completed.',
            'error': 'TOURNAMENT_COMPLETED'
        }), 400

    data = request.get_json() or {}
    team_name = (data.get('team_name') or '').strip()
    captain_name = (data.get('captain_name') or '').strip()
    contact = (data.get('contact') or '').strip()
    player_count = data.get('player_count')
    players = (data.get('players') or '').strip()

    if not team_name or not captain_name or not contact or not player_count:
        return jsonify({
            'success': False,
            'message': 'Team name, captain name, contact number, and player count are required.',
            'error': 'VALIDATION_ERROR'
        }), 400

    try:
        p_count = int(player_count)
        if p_count < 1:
            raise ValueError()
    except (ValueError, TypeError):
        return jsonify({
            'success': False,
            'message': 'Player count must be a positive number.',
            'error': 'INVALID_PLAYER_COUNT'
        }), 400

    # Check for duplicate team name in this tournament
    existing = TournamentRegistration.query.filter(
        TournamentRegistration.tournament_id == tourn.id,
        db.func.lower(TournamentRegistration.team_name) == team_name.lower()
    ).first()

    if existing:
        return jsonify({
            'success': False,
            'message': f'A team named "{team_name}" is already registered in this tournament.',
            'error': 'DUPLICATE_TEAM_NAME'
        }), 400

    ref = generate_registration_reference()
    reg = TournamentRegistration(
        tournament_id=tourn.id,
        user_id=g.current_user.id,
        team_name=team_name,
        captain_name=captain_name,
        contact=contact,
        player_count=p_count,
        players=players,
        registration_reference=ref
    )

    db.session.add(reg)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'Team "{team_name}" successfully registered for {tourn.name}!',
        'data': {
            'registration': reg.to_dict()
        }
    }), 201


@tournament_bp.route('/<int:tournament_id>/registrations', methods=['GET'])
@login_required
def get_registrations(tournament_id):
    tourn = db.session.get(Tournament, tournament_id)
    if not tourn:
        return jsonify({
            'success': False,
            'message': 'Tournament not found',
            'error': 'TOURNAMENT_NOT_FOUND'
        }), 404

    regs = TournamentRegistration.query.filter_by(tournament_id=tournament_id).all()
    return jsonify({
        'success': True,
        'data': {
            'tournament_id': tourn.id,
            'tournament_name': tourn.name,
            'registrations': [r.to_dict() for r in regs],
            'count': len(regs)
        }
    }), 200


@tournament_bp.route('', methods=['POST'])
@admin_required
def create_tournament():
    data = request.get_json() or {}
    name = (data.get('name') or '').strip()
    sport = (data.get('sport') or '').strip()
    description = (data.get('description') or '').strip()
    venue = (data.get('venue') or '').strip()
    t_date_str = data.get('tournament_date')
    deadline_str = data.get('registration_deadline')
    entry_fee = data.get('entry_fee')
    max_teams = data.get('max_teams')
    image_url = (data.get('image_url') or '').strip()

    if not all([name, sport, description, venue, t_date_str, deadline_str, entry_fee, max_teams]):
        return jsonify({
            'success': False,
            'message': 'All tournament fields are required.',
            'error': 'VALIDATION_ERROR'
        }), 400

    try:
        t_date = datetime.strptime(t_date_str, '%Y-%m-%d').date()
        deadline = datetime.strptime(deadline_str, '%Y-%m-%d').date()
        fee = float(entry_fee)
        teams = int(max_teams)
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Invalid dates, entry fee, or team count.',
            'error': 'VALIDATION_ERROR'
        }), 400

    if not image_url:
        image_url = "https://images.unsplash.com/photo-1579952363873-27f3bade9f55?auto=format&fit=crop&w=800&q=80"

    tourn = Tournament(
        name=name,
        sport=sport,
        description=description,
        venue=venue,
        tournament_date=t_date,
        registration_deadline=deadline,
        entry_fee=fee,
        max_teams=teams,
        status='OPEN',
        image_url=image_url
    )

    db.session.add(tourn)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'Tournament "{tourn.name}" created successfully.',
        'data': {
            'tournament': tourn.to_dict()
        }
    }), 201


@tournament_bp.route('/<int:tournament_id>', methods=['PUT'])
@admin_required
def update_tournament(tournament_id):
    tourn = db.session.get(Tournament, tournament_id)
    if not tourn:
        return jsonify({
            'success': False,
            'message': 'Tournament not found',
            'error': 'TOURNAMENT_NOT_FOUND'
        }), 404

    data = request.get_json() or {}
    if 'name' in data:
        tourn.name = data['name'].strip()
    if 'sport' in data:
        tourn.sport = data['sport'].strip()
    if 'description' in data:
        tourn.description = data['description'].strip()
    if 'venue' in data:
        tourn.venue = data['venue'].strip()
    if 'tournament_date' in data:
        tourn.tournament_date = datetime.strptime(data['tournament_date'], '%Y-%m-%d').date()
    if 'registration_deadline' in data:
        tourn.registration_deadline = datetime.strptime(data['registration_deadline'], '%Y-%m-%d').date()
    if 'entry_fee' in data:
        tourn.entry_fee = float(data['entry_fee'])
    if 'max_teams' in data:
        tourn.max_teams = int(data['max_teams'])
    if 'status' in data:
        tourn.status = data['status'].upper()
    if 'image_url' in data:
        tourn.image_url = data['image_url'].strip()

    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'Tournament "{tourn.name}" updated successfully.',
        'data': {
            'tournament': tourn.to_dict()
        }
    }), 200


@tournament_bp.route('/<int:tournament_id>', methods=['DELETE'])
@admin_required
def delete_tournament(tournament_id):
    tourn = db.session.get(Tournament, tournament_id)
    if not tourn:
        return jsonify({
            'success': False,
            'message': 'Tournament not found',
            'error': 'TOURNAMENT_NOT_FOUND'
        }), 404

    db.session.delete(tourn)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'Tournament "{tourn.name}" deleted successfully.'
    }), 200
