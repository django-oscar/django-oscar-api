from rest_framework import generics
from rest_framework.response import Response

from oscar.core.loading import get_class, get_model

from oscarapi import serializers


Selector = get_class('partner.strategy', 'Selector')

__all__ = (
    'ProductList', 'ProductDetail',
    'ProductPrice', 'ProductAvailability',
)

Product = get_model('catalogue', 'Product')


class ProductList(generics.ListAPIView):
    queryset = Product.objects.all()
    serializer_class = serializers.ProductLinkSerializer

    def get_queryset(self):
        """
        Allow filtering on structure so standalone and parent products can
        be selected separately, eg::

            http://127.0.0.1:8000/api/products/?structure=standalone

        or::

            http://127.0.0.1:8000/api/products/?structure=parent
        """
        qs = super(ProductList, self).get_queryset()
        structure = self.request.query_params.get('structure')
        if structure is not None:
            return qs.filter(structure=structure)

        return qs


class ProductDetail(generics.RetrieveAPIView):
    queryset = Product.objects.all()
    serializer_class = serializers.ProductSerializer


class ProductPrice(generics.RetrieveAPIView):
    queryset = Product.objects.all()

    def get(self, request, pk=None, format=None):
        product = self.get_object()
        strategy = Selector().strategy(request=request, user=request.user)
        ser = serializers.PriceSerializer(
            strategy.fetch_for_product(product).price,
            context={'request': request})
        return Response(ser.data)


class ProductAvailability(generics.RetrieveAPIView):
    queryset = Product.objects.all()

    def get(self, request, pk=None, format=None):
        product = self.get_object()
        strategy = Selector().strategy(request=request, user=request.user)
        ser = serializers.AvailabilitySerializer(
            strategy.fetch_for_product(product).availability,
            context={'request': request})
        return Response(ser.data)
