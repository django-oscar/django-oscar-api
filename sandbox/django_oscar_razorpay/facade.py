import logging
from uuid import uuid4

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

from .models import RazorpayTransaction as Transaction
from .exceptions import RazorpayError

import razorpay

# Initialize the Razorpay client with API credentials
rz_client = razorpay.Client(
    auth=(settings.RAZORPAY_API_KEY, settings.RAZORPAY_API_SECRET)
)

logger = logging.getLogger('razorpay')


def start_razorpay_txn(basket, amount, user=None, email=None):
    """
    Record the start of a transaction and calculate costs, etc.
    """
    currency = basket.currency or getattr(settings, 'RAZORPAY_CURRENCY', 'INR')

    # Create a new transaction record
    transaction = Transaction(
        user=user,
        amount=amount,
        currency=currency,
        basket_id=basket.id,
        txnid=uuid4().hex[:28],  # Generate a unique transaction ID
        email=email
    )
    transaction.save()

    logger.info(f"Started Razorpay transaction {transaction.txnid} for basket {basket.id} with amount {amount} {currency}")
    
    return transaction


def update_transaction_details(rz_id, txn_id):
    """
    Fetch the completed details about the Razorpay transaction and update our
    transaction model.
    """
    try:
        # Fetch payment details from Razorpay
        payment = rz_client.payment.fetch(rz_id)
    except razorpay.errors.RazorpayError as e:
        logger.warning(f"Unable to fetch transaction details for Razorpay txn {rz_id}: {e}")
        raise RazorpayError("Failed to fetch transaction details from Razorpay")

    try:
        # Fetch the corresponding transaction from the database
        txn = Transaction.objects.get(txnid=txn_id)
    except ObjectDoesNotExist as e:
        logger.warning(f"Unable to find transaction details for txnid {txn_id}: {e}")
        raise RazorpayError("Transaction not found in the database")

    # Ensure amount and currency match between the Razorpay payment and our transaction record
    if int(txn.amount * 100) != payment["amount"] or txn.currency != payment["currency"]:
        logger.warning(f"Payment details mismatch for txn {txn.txnid} and Razorpay payment {rz_id}")
        raise RazorpayError("Transaction details mismatch")

    # Update the transaction status and Razorpay ID
    txn.status = payment["status"]
    txn.rz_id = rz_id
    txn.save()

    logger.info(f"Updated transaction {txn.txnid} with status {txn.status}")

    return txn


def capture_transaction(rz_id):
    """
    Capture the payment for a given Razorpay transaction ID.
    """
    try:
        # Fetch the transaction from the database
        txn = Transaction.objects.get(rz_id=rz_id)

        # Capture the payment via Razorpay
        if rz_client.payment.fetch(rz_id):
            # Update the transaction status to "captured"
            txn.status = "captured"
            txn.save()

        logger.info(f"Captured payment for transaction {txn.txnid}")
    except ObjectDoesNotExist:
        logger.error(f"Transaction with Razorpay ID {rz_id} not found")
        raise RazorpayError("Transaction not found")
    except razorpay.errors.RazorpayError as e:
        logger.error(f"Couldn't capture payment for transaction {txn.txnid}: {e}")
        raise RazorpayError(f"Failed to capture payment for {txn.txnid}")
    except Exception as e:
        logger.error(f"Unexpected error while capturing payment for transaction {txn.txnid}: {e}")
        raise RazorpayError(f"Error capturing payment for {txn.txnid}")

    return txn


def refund_transaction(rz_id, amount, currency):
    """
    Refund a given amount of the payment for a specific Razorpay transaction.
    """
    try:
        # Fetch the transaction from the database
        txn = Transaction.objects.get(rz_id=rz_id)

        # Ensure the refund amount is less than or equal to the transaction amount
        if amount > int(txn.amount * 100):
            raise RazorpayError("Refund amount exceeds the original transaction amount")

        # Ensure the currency matches the original transaction currency
        if currency != txn.currency:
            raise RazorpayError("Currency mismatch for the refund")

        # Initiate the refund via Razorpay
        rz_client.payment.refund(rz_id, amount)

        logger.info(f"Refunded {amount / 100:.2f} {currency} for transaction {txn.txnid}")

    except ObjectDoesNotExist:
        logger.error(f"Transaction with Razorpay ID {rz_id} not found")
        raise RazorpayError("Transaction not found")
    except razorpay.errors.RazorpayError as e:
        logger.error(f"Couldn't refund transaction {rz_id}: {e}")
        raise RazorpayError(f"Failed to refund transaction {rz_id}")
    except Exception as e:
        logger.error(f"Unexpected error while refunding transaction {rz_id}: {e}")
        raise RazorpayError(f"Error refunding transaction {rz_id}")