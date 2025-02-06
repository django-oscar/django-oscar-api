from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
import warnings

class PaymentAPIView(APIView):
    def get(self, request, pk):
        # Fetch the object related to the payment (e.g., an Order)
        # obj = get_object_or_404(, pk=pk)

        try:
            # Call your payment provider API and get the payment URL
            data = self.initiate_payment(pk)

            # Return the payment URL in the response
            return Response(data, status=status.HTTP_200_OK)

        except Exception as e:
            msg = (
                f"An error occurred while processing the payment: {str(e)}"
            )
            warnings.warn(msg, stacklevel=2)
            return Response({'error': msg}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def initiate_payment(self, obj):
        # Implement the logic to communicate with your payment provider here
        # This is just a placeholder. You need to replace it with actual logic.
        # For example, creating a payment session and returning the payment URL.
        
        # Here, you might want to interact with your payment provider's SDK or API.
        
        # Example of payment URL (replace with actual logic)
        return {
            "key": "rzp_test_Cpsc2xluAYLfSK",
            "amount": "50000",
            "currency": "INR",
            "name": "ORG_NAME",
            "description": "ORG_DESC",
            "image": "ORG_LOGO",
            "order_id": "order_PkWEQgygBJVG63",
            "callback_url": "www.google.com",
            "prefill": {
                "name": "Gagan Bhuva",
                "email": "gagan.bhuva@gmail.com",
                "contact": "8320017842"
            },
            "notes": {
                "note 1": "Some notes "
            },
            "theme": {
                "color": "#f9a758"
            }
        }