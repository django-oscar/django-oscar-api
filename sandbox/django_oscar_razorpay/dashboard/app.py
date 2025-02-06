from django.urls import path, re_path
from django.contrib.admin.views.decorators import staff_member_required

from oscar.core.application import OscarConfig

from . import views


class RazorpayDashboardApplication(OscarConfig):
    name = None
    list_view = views.TransactionListView
    detail_view = views.TransactionDetailView

    def get_urls(self):
        urlpatterns = [
            path('transactions/', self.list_view.as_view(), name='razorpay-list'),
            re_path(r'^transactions/(?P<pk>\d+)/$', self.detail_view.as_view(), name='razorpay-detail'),
        ]
        return self.post_process_urls(urlpatterns)

    def get_url_decorator(self, url_name):
        return staff_member_required


application = RazorpayDashboardApplication()
