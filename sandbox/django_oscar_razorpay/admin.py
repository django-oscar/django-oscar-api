from django.contrib import admin
from .models import RazorpayTransaction


class RazorpayTransactionAdmin(admin.ModelAdmin):
    # Fields to display in the list view
    list_display = [
        'user', 'amount', 'currency', 'txnid', 'status',
        'rz_id', 'error_code', 'error_message', 'date_created',
        'basket_id', 'email'
    ]

    # Fields to make read-only in the detailed view
    readonly_fields = [
        'user', 'amount', 'currency', 'txnid', 'rz_id',
        'error_code', 'error_message', 'date_created',
        'basket_id', 'email'
    ]

    # Enable search on these fields
    search_fields = ['txnid', 'rz_id', 'email', 'user__username']

    # Enable filtering by these fields
    list_filter = ['status', 'currency', 'date_created']

    # Order by date created (most recent first)
    ordering = ['-date_created']


# Register the model with the admin site
admin.site.register(RazorpayTransaction, RazorpayTransactionAdmin)