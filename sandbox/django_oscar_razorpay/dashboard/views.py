from django.views import generic
from .. import models


class TransactionListView(generic.ListView):
    model = models.RazorpayTransaction
    template_name = 'rzpay/dashboard/transaction_list.html'
    context_object_name = 'transactions'
    paginate_by = 10  # Optional: Adds pagination


class TransactionDetailView(generic.DetailView):
    model = models.RazorpayTransaction
    template_name = 'rzpay/dashboard/transaction_detail.html'
    context_object_name = 'txn'

    def get_context_data(self, **kwargs):
        # Optionally, add more context to be passed to the template
        context = super().get_context_data(**kwargs)
        context['additional_data'] = 'Some extra data'
        return context
