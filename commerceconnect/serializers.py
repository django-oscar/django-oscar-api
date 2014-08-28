from django.db.models.loading import get_model

from rest_framework import serializers

Basket = get_model('basket', 'Basket')
Line = get_model('basket', 'Line')
LineAttribute = get_model('basket', 'LineAttribute')
Product = get_model('catalogue', 'Product')
StockRecord = get_model('partner', 'StockRecord')


class BasketSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Basket
        fields = ['id', 'owner', 'status', 'vouchers', 'lines']


class LineSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Line


class LineAttributeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = LineAttribute


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product


class StockRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockRecord