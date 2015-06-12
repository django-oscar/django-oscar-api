# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from rest_framework import filters

from oscar.core.loading import get_model

Product = get_model('catalogue', 'Product')


class FilterProductCategoryBackend(filters.DjangoFilterBackend):
    """
    Filter backend by category_id
    """
    class Meta:
        model = Product

    def filter_queryset(self, request, queryset, view):
        queryset = super(
            FilterProductCategoryBackend, self).filter_queryset(
            request, queryset, view)

        category_id = request.QUERY_PARAMS.get('category_id', None)
        if category_id:
            queryset = queryset.filter(productcategory__category_id=category_id)
        return queryset
