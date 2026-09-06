import re
from datetime import date, timedelta
from flask import Blueprint, request, jsonify
from app.models import db, Turf, Tournament, Booking
from app.auth import get_current_user

chatbot_bp = Blueprint('chatbot', __name__, url_prefix='/api/chatbot')


@chatbot_bp.route('/message', methods=['POST'])
def chat_message():
    data = request.get_json() or {}
    user_msg = (data.get('message') or '').strip().lower()
    current_user = get_current_user()

    if not user_msg:
        return jsonify({
            'success': False,
            'message': 'Please provide a message.',
            'error': 'EMPTY_MESSAGE'
        }), 400

    reply = ""
    cards = []
    quick_replies = [
        "⚽ Find Football Turfs",
        "🏏 Find Cricket Turfs",
        "💰 Cheapest Turfs",
        "🏆 Upcoming Tournaments",
        "📅 How to Book & Cancel"
    ]

    # Intent 1: Greetings
    if any(greet in user_msg for greet in ['hello', 'hi', 'hey', 'greetings', 'start', 'help']):
        user_name = f" {current_user.name}" if current_user else ""
        reply = (
            f"👋 Hello{user_name}! Welcome to **TurfZone** — your all-in-one sports turf booking and tournament platform.\n\n"
            "Here is what I can help you with right now:\n"
            "• **Find sports turfs** by sport (*Football, Cricket, Badminton, Tennis*)\n"
            "• **Locate venues** across Chennai (*Velachery, Marina, ECR, Anna Nagar, OMR, T. Nagar*)\n"
            "• **Compare prices** and find the most affordable slots\n"
            "• **Check upcoming tournaments** and prize pools\n"
            "• **Track your reservations** or understand our cancellation policy\n\n"
            "How can I assist your game today?"
        )

    # Intent 2: My Bookings
    elif any(b_kw in user_msg for b_kw in ['my booking', 'my reservations', 'view my bookings', 'active bookings', 'check booking']):
        if not current_user:
            reply = "🔒 You need to be logged in to view your bookings. Please [log in here](/login) to check your upcoming matches and reservation history."
            quick_replies = ["🔑 Log In", "⚽ Browse Turfs", "🏆 Tournaments"]
        else:
            today = date.today()
            bookings = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.booking_date.desc()).all()
            if not bookings:
                reply = f"You don't have any bookings yet, **{current_user.name}**! Check out our [Explore Turfs](/turfs) page to find an available arena near you."
            else:
                upcoming = [b for b in bookings if b.status == 'CONFIRMED' and b.booking_date >= today]
                reply = f"📋 Found **{len(bookings)}** total bookings for your account (**{len(upcoming)}** upcoming):\n\n"
                for b in bookings[:4]:
                    status_badge = "🟢 CONFIRMED" if b.status == 'CONFIRMED' else ("🔴 CANCELLED" if b.status == 'CANCELLED' else "🔵 COMPLETED")
                    reply += f"• **{b.booking_reference}**: *{b.turf.name}* on **{b.booking_date.strftime('%b %d, %Y')}** ({b.slot.start_time}-{b.slot.end_time}) — {status_badge}\n"
                reply += "\n👉 You can manage or cancel reservations in [My Bookings](/bookings)."
                quick_replies = ["📅 View All Bookings", "⚽ Book New Turf", "🏆 Tournaments"]

    # Intent 3: Cancellation policy
    elif any(c_kw in user_msg for c_kw in ['cancel', 'cancellation', 'refund', 'reschedule']):
        reply = (
            "🔄 **How TurfZone Booking Cancellation Works:**\n\n"
            "1. Navigate to your [My Bookings](/bookings) dashboard.\n"
            "2. Locate your active booking under the **Upcoming** tab.\n"
            "3. Click the **Cancel Booking** button and confirm.\n"
            "4. Your booking status will immediately update to `CANCELLED`, and the time slot will be instantly released for other players.\n\n"
            "⚠️ *Note: Completed or past bookings cannot be cancelled.*"
        )
        quick_replies = ["📅 My Bookings", "⚽ Explore Turfs", "💰 Pricing"]

    # Intent 4: Cheapest / Price / Cost
    elif any(p_kw in user_msg for p_kw in ['cheap', 'cheapest', 'lowest price', 'affordable', 'price', 'rates', 'cost']):
        turfs = Turf.query.filter_by(is_active=True).order_by(Turf.price_per_hour.asc()).limit(3).all()
        reply = "💰 Here are our most affordable sports turfs in Chennai:\n\n"
        for t in turfs:
            reply += f"• **[{t.name}](/turf/{t.id})** ({t.location}) — **₹{int(t.price_per_hour)}/hour** ⭐ {t.rating}/5.0\n  *Sports: {t.sport}*\n\n"
        reply += "💡 Click on any turf to view available hourly slots and book directly!"
        cards = [t.to_dict() for t in turfs]
        quick_replies = ["⚽ Football Turfs", "🏏 Cricket Turfs", "🏆 Tournaments"]

    # Intent 5: Specific Sport
    elif any(s_kw in user_msg for s_kw in ['football', 'soccer', 'futsal', 'cricket', 'box cricket', 'badminton', 'tennis', 'basketball']):
        detected_sport = 'Football'
        if 'cricket' in user_msg:
            detected_sport = 'Cricket'
        elif 'badminton' in user_msg:
            detected_sport = 'Badminton'
        elif 'tennis' in user_msg:
            detected_sport = 'Tennis'
        elif 'basketball' in user_msg:
            detected_sport = 'Basketball'

        turfs = Turf.query.filter(
            Turf.is_active == True,
            db.func.lower(Turf.sport).contains(detected_sport.lower())
        ).order_by(Turf.rating.desc()).limit(3).all()

        if turfs:
            reply = f"⚡ Top **{detected_sport}** venues available on TurfZone:\n\n"
            for t in turfs:
                reply += f"• **[{t.name}](/turf/{t.id})** in {t.location} — **₹{int(t.price_per_hour)}/hr** (⭐ {t.rating})\n  *Amenities: {', '.join(t.facilities.split(',')[:3])}*\n\n"
            reply += f"🔍 Want to see more? View all [{detected_sport} Turfs](/turfs?sport={detected_sport})."
            cards = [t.to_dict() for t in turfs]
        else:
            reply = f"We couldn't find specific turfs for '{detected_sport}'. Explore our complete directory on [Explore Turfs](/turfs)."

    # Intent 6: Location
    elif any(loc in user_msg for loc in ['velachery', 'marina', 'ecr', 'anna nagar', 'omr', 't. nagar', 't nagar', 'chennai']):
        loc_match = ""
        for loc in ['velachery', 'marina', 'ecr', 'anna nagar', 'omr', 't nagar']:
            if loc in user_msg:
                loc_match = loc.replace('t nagar', 't. nagar')
                break

        query = Turf.query.filter_by(is_active=True)
        if loc_match:
            query = query.filter(db.func.lower(Turf.location).contains(loc_match))
        turfs = query.limit(3).all()

        if turfs:
            reply = f"📍 Found these venues near **{loc_match.title() if loc_match else 'Chennai'}**:\n\n"
            for t in turfs:
                reply += f"• **[{t.name}](/turf/{t.id})** — {t.address}\n  *Price: ₹{int(t.price_per_hour)}/hr | ⭐ {t.rating}*\n\n"
            cards = [t.to_dict() for t in turfs]
        else:
            reply = "Explore our verified Chennai turf directory with live slot booking on [Explore Turfs](/turfs)."

    # Intent 7: Tournaments
    elif any(t_kw in user_msg for t_kw in ['tournament', 'league', 'cup', 'contest', 'championship', 'register team']):
        tournaments = Tournament.query.filter(Tournament.status.in_(['OPEN', 'FULL'])).order_by(Tournament.tournament_date.asc()).limit(3).all()
        reply = "🏆 **Upcoming TurfZone Tournaments & Championships:**\n\n"
        for tourn in tournaments:
            status_text = "🟢 OPEN FOR REGISTRATION" if tourn.status == 'OPEN' else "🔴 REGISTRATION FULL"
            reply += f"• **{tourn.name}** ({tourn.sport})\n  📅 Date: **{tourn.tournament_date.strftime('%b %d, %Y')}** | 📍 Venue: *{tourn.venue}*\n  💵 Entry Fee: ₹{int(tourn.entry_fee)} | {status_text}\n\n"
        reply += "👉 Register your squad on the [Tournaments](/tournaments) page before slots run out!"
        quick_replies = ["🏆 View All Tournaments", "⚽ Explore Turfs", "💰 Pricing"]

    # Default fallback
    else:
        turfs = Turf.query.filter_by(is_active=True).order_by(Turf.rating.desc()).limit(2).all()
        reply = (
            "I'm here to help you find turfs, compare rates, check availability, track bookings, and explore competitive tournaments in Chennai!\n\n"
            "Try asking me:\n"
            "• *'Find top football turfs in Velachery'*\n"
            "• *'Show cheapest cricket turfs'*\n"
            "• *'What tournaments are coming up?'*\n"
            "• *'Check my active bookings'*"
        )
        cards = [t.to_dict() for t in turfs]

    return jsonify({
        'success': True,
        'data': {
            'reply': reply,
            'quick_replies': quick_replies,
            'cards': cards
        }
    }), 200
