# TurfZone — Production-Style Sports Facility & Turf Booking Platform

> **Book Your Turf. Play Your Game.**

TurfZone is a complete, realistic, full-stack sports facility marketplace, real-time reservation engine, and tournament management platform built for athletes, teams, and facility owners across Chennai.

---

## 🌟 Key Highlights & Core Features

- **🏟️ Verified Facility Marketplace**: Discover sports arenas across prime Chennai neighborhoods (Velachery, Marina Beach, ECR, Anna Nagar, OMR, T. Nagar) with dynamic filtering by sport, location, price slider, and ratings.
- **⚡ Transaction-Safe Booking Engine**: Real-time slot availability computed directly from database records. **Strict concurrency locking guarantees zero double-bookings (HTTP 409 Conflict rejection)**.
- **🔄 Instant Self-Service Cancellation**: Athletes can cancel reservations from their dashboard with immediate slot release and database status tracking (`CONFIRMED` → `CANCELLED`).
- **🏆 City Tournaments & Squad Registration**: Discover upcoming championships with capacity tracking, team registration, roster submission, and automatic capacity validation.
- **🤖 Turf-Bot AI Assistant**: Intelligent chatbot querying live database records for cheapest grounds, sport-specific arenas, open tournament slots, and booking policies without requiring paid third-party APIs.
- **🛡️ Admin Operations Control Center**: Comprehensive operations dashboard featuring real revenue calculation, turf CRUD with instant marketplace sync, booking status controls, tournament orchestration, and athlete directory.
- **🔐 Secure Authentication**: Werkzeug password hashing, stateless cryptographically signed Bearer tokens, client & server-side validation, and role-based access control.

---

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| **Frontend** | HTML5, CSS3 Custom Modern Dark Design System, Vanilla JavaScript (ES6+), Fetch API |
| **Backend** | Python 3.14, Flask, Flask-SQLAlchemy, Flask-CORS, Werkzeug Security, itsdangerous |
| **Database** | SQLite (relational ORM with indexed constraints, compatible with PostgreSQL) |
| **Testing** | Python `unittest` suite covering Auth, Turfs, Booking Concurrency, Tournaments, Admin, and Chatbot |
| **API Testing** | `Postman_Collection.json` compatible with Postman, Insomnia, and cURL |

---

## 📂 Project Architecture & Directory Structure

```
turfzone/
├── app/
│   ├── __init__.py            # Flask application factory, DB init, CORS, Blueprints, seeding
│   ├── models.py              # User, Turf, TimeSlot, Booking, Tournament, TournamentRegistration
│   ├── auth.py                # Token generation, verification, @login_required, @admin_required
│   ├── seed.py                # Authentic Chennai venues, default slots, tournaments & demo data
│   └── routes/
│       ├── auth_routes.py     # /api/auth (register, login, me, profile, logout)
│       ├── turf_routes.py     # /api/turfs (search, filter, sort, slots, availability)
│       ├── booking_routes.py  # /api/bookings (create with 409 conflict checks, user list, cancel)
│       ├── tournament_routes.py # /api/tournaments (list, register team, admin management)
│       ├── admin_routes.py    # /api/admin/stats, users, bookings management, tournament CRUD
│       ├── chatbot_routes.py  # /api/chatbot/message (smart database query & assistant engine)
│       └── frontend_routes.py # HTML view rendering routes
├── static/
│   ├── css/
│   │   └── styles.css         # Modern dark sports design system, badges, toasts, responsive UI
│   └── js/
│       ├── api.js             # API helper, auth headers, toast alerts, loading spinners
│       ├── auth.js            # Auth state, dynamic navigation bar, login/register handlers
│       ├── main.js            # Global components (toasts, modals, drawer, formatters)
│       ├── home.js            # Landing page hero search, sports category pills, featured cards
│       ├── turfs.js           # Marketplace filter sidebar, live search, sorting, turf cards
│       ├── turf-detail.js     # Image gallery, date picker, live slot grid, booking modal & API
│       ├── bookings.js        # My Bookings (Upcoming/Current/Previous tabs, cancellation modal)
│       ├── tournaments.js     # Tournament cards, team registration modal, validation
│       ├── dashboard.js       # User dashboard metrics, upcoming booking hero, quick actions
│       ├── profile.js         # User profile data, edit profile, change password
│       ├── turf-bot.js        # Assistant chat interface, quick chips, database-driven cards
│       └── admin.js           # Admin control center, stats, turf/booking/tournament/user CRUD
├── templates/
│   ├── base.html              # Core navigation, toast container, modals, footer
│   ├── index.html             # Landing / Home page
│   ├── turfs.html             # Turf discovery / marketplace
│   ├── turf-detail.html       # Turf detail & interactive slot booking
│   ├── tournaments.html       # Tournaments listing & team registration
│   ├── dashboard.html         # User dashboard
│   ├── bookings.html          # My bookings management
│   ├── profile.html           # User profile & settings
│   ├── turf-bot.html          # Turf-Bot AI assistant page
│   ├── login.html             # Login page
│   ├── register.html          # Register page
│   └── admin.html             # Admin control center
├── tests/
│   └── test_turfzone.py       # Comprehensive automated test suite
├── Postman_Collection.json    # Complete Postman API collection
├── requirements.txt           # Python dependencies
├── run.py                     # Main application entry point (port 5000)
└── README.md                  # Complete documentation
```

---

## 🗄️ Relational Database Schema

```
+-----------------------------------------------------------------------------------+
|                                      USERS                                        |
| id (PK) | name | email (UQ, IDX) | phone | password_hash | role | is_active | ... |
+-----------------------------------------------------------------------------------+
                                   | 1:N
                                   v
+-----------------------------------------------------------------------------------+
|                                     BOOKINGS                                      |
| id (PK) | booking_ref (UQ) | user_id (FK) | turf_id (FK) | slot_id (FK)           |
| booking_date (IDX) | sport | price | status (CONFIRMED/CANCELLED/COMPLETED)       |
+-----------------------------------------------------------------------------------+
                                   ^
                                   | N:1
+-----------------------------------------------------------------------------------+
|                                      TURFS                                        |
| id (PK) | name | location | address | sport | description | facilities             |
| price_per_hour | rating | reviews_count | image_url | is_active | created_at      |
+-----------------------------------------------------------------------------------+
                                   | 1:N
                                   v
+-----------------------------------------------------------------------------------+
|                                   TIME_SLOTS                                      |
| id (PK) | turf_id (FK) | start_time ("09:00") | end_time ("10:00")                |
+-----------------------------------------------------------------------------------+

+-----------------------------------------------------------------------------------+
|                                   TOURNAMENTS                                     |
| id (PK) | name | sport | description | venue | tournament_date | deadline         |
| entry_fee | max_teams | status (OPEN/FULL/CLOSED/COMPLETED) | image_url           |
+-----------------------------------------------------------------------------------+
                                   | 1:N
                                   v
+-----------------------------------------------------------------------------------+
|                             TOURNAMENT_REGISTRATIONS                              |
| id (PK) | tournament_id (FK) | user_id (FK) | team_name | captain_name            |
| contact | player_count | players | registration_reference (UQ)                    |
+-----------------------------------------------------------------------------------+
```

---

## 🚀 Quick Start & Installation

### 1. Install Dependencies
```powershell
python -m pip install -r requirements.txt
```

### 2. Start Application Server
```powershell
python run.py
```

### 3. Open Web Application
Navigate in your browser to:
👉 **`http://127.0.0.1:5000`**

---

## 🔑 Demo Accounts & Credentials

The database is automatically pre-seeded on initial startup with realistic Chennai venues, slots, tournaments, and demo accounts:

| Role | Email | Password | Access Privileges |
|---|---|---|---|
| **Administrator** | `admin@turfzone.com` | `Admin@123` | Full admin control, revenue stats, turf/tournament CRUD, bookings control |
| **Athlete (User)** | `user@turfzone.com` | `User@123` | Booking slots, managing reservations, team tournament registration, profile |
| **Athlete 2** | `rahul@turfzone.com` | `User@123` | Secondary user for testing multi-user reservation conflict scenarios |

---

## 🧪 Automated Testing Suite

Run the full test suite covering Auth, Turfs, Concurrency Conflict Rejections, Slot Release on Cancellation, Tournaments, Admin Statistics, and Turf-Bot:

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

---

## 📡 REST API Reference

### Authentication (`/api/auth`)
- `POST /api/auth/register` — Register a new athlete account.
- `POST /api/auth/login` — Authenticate and receive session token.
- `GET /api/auth/me` — Get current logged-in user profile.
- `PUT /api/auth/profile` — Update personal info or change password.
- `POST /api/auth/logout` — Invalidate user session.

### Turfs (`/api/turfs`)
- `GET /api/turfs` — Search, filter, and sort all active sports turfs.
- `GET /api/turfs/<id>` — Get single turf details with all time slots.
- `GET /api/turfs/<id>/slots` — Get list of configured time slots.
- `GET /api/turfs/<id>/availability?date=YYYY-MM-DD` — Real-time slot availability for a specific date.
- `POST /api/turfs` *(Admin)* — Create new facility (auto-generates hourly slots).
- `PUT /api/turfs/<id>` *(Admin)* — Update facility information or toggle status.
- `DELETE /api/turfs/<id>` *(Admin)* — Delete or deactivate facility.

### Bookings Engine (`/api/bookings`)
- `POST /api/bookings` — Reserve a slot. **Returns HTTP 409 Conflict if slot is already reserved**.
- `GET /api/bookings` — Get current user's reservations (tabbed by upcoming, current, previous).
- `GET /api/bookings/<id>` — Get single reservation details.
- `PUT /api/bookings/<id>/cancel` — Cancel reservation, mark status as `CANCELLED`, and release slot.

### Tournaments (`/api/tournaments`)
- `GET /api/tournaments` — List all upcoming tournaments with dynamic status & team capacity.
- `GET /api/tournaments/<id>` — Tournament details and registered team list.
- `POST /api/tournaments/<id>/register` — Register a squad (validates deadline, capacity, duplicate team).
- `POST /api/tournaments` *(Admin)* — Create new tournament.
- `PUT /api/tournaments/<id>` *(Admin)* — Update tournament details.
- `DELETE /api/tournaments/<id>` *(Admin)* — Delete tournament.

### Admin Operations (`/api/admin`)
- `GET /api/admin/stats` — Platform KPIs: Revenue, Total Bookings, Today's Matches, Active Turfs.
- `GET /api/admin/users` — List all registered users with booking stats.
- `PUT /api/admin/users/<id>/toggle-status` — Activate / Deactivate user accounts.
- `GET /api/admin/bookings` — Full reservation log with status filtering.
- `PUT /api/admin/bookings/<id>/status` — Update booking status (`CONFIRMED`, `COMPLETED`, `CANCELLED`).

### Turf-Bot Assistant (`/api/chatbot`)
- `POST /api/chatbot/message` — Send queries to Turf-Bot for instant database-backed answers.

---

## 📬 Postman Collection

Import `Postman_Collection.json` into Postman or Insomnia. It includes pre-configured endpoints, request bodies, and variable tokens for quick testing.
## Booking Feature
TurfZone supports online turf slot booking.
