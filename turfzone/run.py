import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"==================================================")
    print(f" TurfZone — Production-Style Sports Booking Engine ")
    print(f" Running at: http://127.0.0.1:{port}")
    print(f" Demo Admin: admin@turfzone.com | Admin@123")
    print(f" Demo User:  user@turfzone.com  | User@123")
    print(f"==================================================")
    app.run(host='127.0.0.1', port=port, debug=True)
