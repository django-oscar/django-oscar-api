import uuid
from django.db import models
from django.conf import settings


def generate_id():
    return uuid.uuid4().hex[:28]


class RazorpayTransaction(models.Model):
    date_created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    email = models.EmailField(null=True, blank=True)

    txnid = models.CharField(max_length=32, db_index=True, default=generate_id)

    basket_id = models.CharField(max_length=12, null=True, blank=True, db_index=True)

    amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=8, null=True, blank=True)

    # Status choices for better clarity and validation
    INITIATED = "initiated"
    CAPTURED = "captured"
    AUTHORIZED = "authorized"
    CAPTURE_FAILED = "capfailed"
    AUTH_FAILED = "authfailed"

    STATUS_CHOICES = [
        (INITIATED, "Initiated"),
        (CAPTURED, "Captured"),
        (AUTHORIZED, "Authorized"),
        (CAPTURE_FAILED, "Capture Failed"),
        (AUTH_FAILED, "Authorization Failed"),
    ]

    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=INITIATED)

    rz_id = models.CharField(max_length=32, null=True, blank=True, db_index=True)

    error_code = models.CharField(max_length=32, null=True, blank=True)
    error_message = models.CharField(max_length=256, null=True, blank=True)

    class Meta:
        ordering = ('-date_created',)

    @property
    def is_successful(self):
        return self.status == self.CAPTURED

    @property
    def is_pending(self):
        return self.status == self.AUTHORIZED

    @property
    def is_failed(self):
        return self.status not in (self.CAPTURED, self.AUTHORIZED, self.INITIATED)

    def __str__(self):
        return f'Razorpay payment: {self.rz_id or self.txnid}'