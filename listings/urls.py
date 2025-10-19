from django.urls import path
from . import views
urlpatterns = [
    path('book/', views.create_booking, name='create_booking'),
    path('payment/initiate/<int:booking_id>/', views.initiate_payment, name='initiate_payment'),
    path('payment/verify/<int:payment_id>/', views.verify_payment, name='verify_payment'),
]
