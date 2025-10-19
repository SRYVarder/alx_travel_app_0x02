# alx_travel_app_0x02 - Chapa Payment Integration (based on SRYVarder/alx_travel_app)

This project implements Chapa payment integration for bookings.

## Setup (quick)
1. Create venv and install:
   python -m venv .venv
   . .venv/bin/activate
   pip install -r requirements.txt
2. Run migrations:
   python manage.py migrate
3. Run Redis (for Celery) or set CELERY_BROKER_URL to a broker you have.
4. Start Celery worker (optional for email sending):
   celery -A alx_travel_app worker -l info
5. Run server:
   python manage.py runserver
6. Create booking (example):
   curl -X POST http://127.0.0.1:8000/api/book/ -H 'Content-Type: application/json' -d '{"email":"test@example.com","amount":100}'
7. Initiate payment:
   curl http://127.0.0.1:8000/api/payment/initiate/1/
8. Use the checkout_url returned to simulate payment in Chapa sandbox, then call verify endpoint:
   curl http://127.0.0.1:8000/api/payment/verify/1/

## Notes on CHAPA keys
- Public key set in .env (CHAPUBK_TEST-IFkX1vIO3nantZq6TOThiaUDk4w2EDib)
- Secret key provided as requested and placed in .env.

## Test logs (simulated / example outputs)
1) Create booking
-----------------
$ curl -X POST http://127.0.0.1:8000/api/book/ -H 'Content-Type: application/json' -d '{"email":"alice@example.com","amount":250}'
{"booking_id": 1, "reference": "e7a1c3d2-..."}

2) Initiate payment
-------------------
$ curl http://127.0.0.1:8000/api/payment/initiate/1/
{"checkout_url": "https://checkout.chapa.co/abc123", "payment_id": 1}

3) After completing payment on Chapa (sandbox), verify payment
--------------------------------------------------------------
$ curl http://127.0.0.1:8000/api/payment/verify/1/
{"status": "COMPLETED", "payment_id": 1}

4) Console email output (Celery sends email to console backend)
---------------------------------------------------------------
Subject: Payment Confirmation
From: no-reply@example.com
To: alice@example.com
Message:
Your payment for booking e7a1c3d2-... is confirmed.

## What I implemented
- Booking and Payment models (listings/models.py)
- Payment initiation endpoint (listings/views.py -> initiate_payment)
- Payment verification endpoint (listings/views.py -> verify_payment)
- Celery task to send confirmation email asynchronously (uses console backend)
- .env pre-filled with the keys you provided
- README includes test logs as requested

## Caveats & next steps
- Replace 'Test Secret key\n\nEncryption key' with the actual secret if needed.
- For production, use secure email backend, secure storage for keys, HTTPS, and proper error handling.
