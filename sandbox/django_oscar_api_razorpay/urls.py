from django.urls import path
from .views import PaymentAPIView

urlpatterns = [
    path('payment/<int:pk>/', PaymentAPIView.as_view(), name='api-payment'),
]