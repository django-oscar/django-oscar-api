from django.db import models

class EditableBasketManager(models.Manager):
    """For searching/creating editable baskets only."""

    def get_query_set(self):
        return super(EditableBasketManager, self).get_query_set().filter(
            status__in=["Open", "Saved"])

    def get_or_create(self, **kwargs):
        return self.get_query_set().get_or_create(
            status="Open", **kwargs)
