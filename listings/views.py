from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .models import Booking, Payment
import requests, os
from django.core.mail import send_mail
from celery import shared_task
@csrf_exempt
def create_booking(request):
    # Simple booking creation for demo: expects JSON with email and amount
    import json
    data = json.loads(request.body.decode('utf-8'))
    email = data.get('email')
    amount = data.get('amount')
    if not email or not amount:
        return JsonResponse({'error': 'email and amount required'}, status=400)
    booking = Booking.objects.create(user_email=email, amount=amount)
    return JsonResponse({'booking_id': booking.id, 'reference': str(booking.reference)})
@csrf_exempt
def initiate_payment(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    # Create Payment record
    payment = Payment.objects.create(booking=booking, amount=booking.amount, status='PENDING')
    # Prepare payload for Chapa initialize
    chapa_url = 'https://api.chapa.co/v1/transaction/initialize'
    headers = {'Authorization': f'Bearer {settings.CHAPA_SECRET_KEY}', 'Content-Type': 'application/json'}
    callback_url = request.build_absolute_uri(f'/api/payment/verify/{payment.id}/')
    payload = {
        'amount': str(float(payment.amount)),
        'currency': 'ETB',
        'email': booking.user_email,
        'first_name': 'Customer',
        'last_name': 'Name',
        'phone': '',
        'tx_ref': str(payment.id),
        'callback_url': callback_url,
        'return_url': callback_url,
    }
    try:
        resp = requests.post(chapa_url, json=payload, headers=headers, timeout=10)
        data = resp.json()
        # expected structure: { 'data': { 'checkout_url': 'https://...', 'reference': '...' }, 'status': 'success' }
        if resp.status_code == 200 and data.get('data'):
            checkout_url = data['data'].get('checkout_url') or data['data'].get('checkout_url')
            transaction_id = data['data'].get('reference') or data['data'].get('transaction_id') or ''
            payment.transaction_id = transaction_id
            payment.save()
            return JsonResponse({'checkout_url': checkout_url, 'payment_id': payment.id})
        else:
            payment.status = 'FAILED'
            payment.save()
            return JsonResponse({'error': 'Failed to initialize payment', 'details': data}, status=502)
    except Exception as e:
        payment.status = 'FAILED'
        payment.save()
        return JsonResponse({'error': 'Exception calling Chapa', 'details': str(e)}, status=500)
@csrf_exempt
def verify_payment(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    chapa_verify = f'https://api.chapa.co/v1/transaction/verify/{payment.transaction_id or payment.id}'
    headers = {'Authorization': f'Bearer {settings.CHAPA_SECRET_KEY}'}
    try:
        resp = requests.get(chapa_verify, headers=headers, timeout=10)
        data = resp.json()
        # expected: data['data']['status'] == 'paid' or similar
        status = data.get('data', {}).get('status') or data.get('status')
        if status and status.lower() in ('paid', 'success', 'completed'):
            payment.status = 'COMPLETED'
            payment.save()
            # send confirmation email asynchronously
            send_payment_confirmation_email.delay(payment.id)
            return JsonResponse({'status': 'COMPLETED', 'payment_id': payment.id})
        else:
            payment.status = 'FAILED'
            payment.save()
            return JsonResponse({'status': 'FAILED', 'details': data}, status=400)
    except Exception as e:
        return JsonResponse({'error': 'Exception verifying payment', 'details': str(e)}, status=500)
@shared_task
def send_payment_confirmation_email(payment_id):
    try:
        p = Payment.objects.get(id=payment_id)
        send_mail('Payment Confirmation', f'Your payment for booking {p.booking.reference} is confirmed.', 'no-reply@example.com', [p.booking.user_email])
        return True
    except Exception as e:
        return False
