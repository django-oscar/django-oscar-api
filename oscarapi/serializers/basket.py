# pylint: disable=W0223
import logging
from decimal import Decimal

from django.utils.translation import gettext as _
from django.contrib.auth import get_user_model
from rest_framework import serializers

from oscar.core.loading import get_model

from oscarapi import settings
from oscarapi.basket import operations
from oscarapi.serializers.fields import (
    DrillDownHyperlinkedIdentityField,
    DrillDownHyperlinkedRelatedField,
)
from oscarapi.serializers.utils import (
    OscarModelSerializer,
    OscarHyperlinkedModelSerializer,
)
from oscarapi.serializers.fields import TaxIncludedDecimalField
from oscarapi.serializers.product import OptionValueSerializer, ProductSerializer

logger = logging.getLogger(__name__)

User = get_user_model()
Basket = get_model("basket", "Basket")
Line = get_model("basket", "Line")
LineAttribute = get_model("basket", "LineAttribute")
StockRecord = get_model("partner", "StockRecord")
Voucher = get_model("voucher", "Voucher")
Product = get_model("catalogue", "Product")
ProductImage = get_model("catalogue", "ProductImage")

class LineAttributeSerializer(OscarHyperlinkedModelSerializer):
    url = DrillDownHyperlinkedIdentityField(
        view_name="lineattribute-detail",
        extra_url_kwargs={"basket_pk": "line.basket.id", "line_pk": "line.id"},
    )
    line = DrillDownHyperlinkedIdentityField(
        view_name="basket-line-detail", extra_url_kwargs={"basket_pk": "line.basket.id"}
    )
    price = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()

    class Meta:
        model = LineAttribute
        fields = "__all__"  # Include all fields

    def get_price(self, obj):
        """
        Retrieve the price of the related Option.
        """
        try:
           attribute_option = obj.option.option_group.options.get(option=obj.value)  # Retrieve all related AttributeOption objects
           return str(attribute_option.price) 
        except :
            return str(0)
        
    def get_type(self, obj):
        """
        Retrieve the type of the related Option.
        """
        try:
           attribute_option = obj.option.type  # Retrieve all related AttributeOption objects
           return attribute_option 
        except :
            return ""
        
    def get_name(self, obj):
        """
        Retrieve the name of the related Option.
        """
        try:
           attribute_option = obj.option.name  # Retrieve all related AttributeOption objects
           return attribute_option 
        except :
            return ""


class VoucherSerializer(OscarModelSerializer):
    class Meta:
        model = Voucher
        fields = settings.VOUCHER_FIELDS


class OfferDiscountSerializer(
    serializers.Serializer
):  # pylint: disable=abstract-method
    description = serializers.CharField()
    name = serializers.CharField()
    amount = serializers.DecimalField(
        decimal_places=2, max_digits=12, source="discount"
    )


class VoucherDiscountSerializer(OfferDiscountSerializer):
    voucher = VoucherSerializer(required=False)
    
    
class AbstractLineSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)  # Nested serializer for the product field
    attributes = LineAttributeSerializer(
        many=True, fields=("id", "option", "value","price","type","name"), required=False, read_only=True
    )
    class Meta:
        model = Line
        fields = [
            'id',
            'product',  # This will now include all fields of the product
            'quantity',
            'attributes'
        ]
class ProductInBasketSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    qty = serializers.IntegerField()
    line_id = serializers.IntegerField()

    
    
class BasketSerializer(serializers.HyperlinkedModelSerializer):
    lines = AbstractLineSerializer(many=True, read_only=True)
    offer_discounts = OfferDiscountSerializer(many=True, required=False)
    total_excl_tax = serializers.DecimalField(
        decimal_places=2, max_digits=12, required=False
    )
    total_excl_tax_excl_discounts = serializers.DecimalField(
        decimal_places=2, max_digits=12, required=False
    )
    total_incl_tax = TaxIncludedDecimalField(
        excl_tax_field="total_excl_tax", decimal_places=2, max_digits=12, required=False
    )
    total_incl_tax_excl_discounts = TaxIncludedDecimalField(
        excl_tax_field="total_excl_tax_excl_discounts",
        decimal_places=2,
        max_digits=12,
        required=False,
    )
    total_tax = TaxIncludedDecimalField(
        excl_tax_value=Decimal("0.00"), decimal_places=2, max_digits=12, required=False
    )
    currency = serializers.CharField(required=False)
    voucher_discounts = VoucherDiscountSerializer(many=True, required=False)
    owner = serializers.HyperlinkedRelatedField(
        view_name="user-detail",
        required=False,
        allow_null=True,
        queryset=User.objects.all(),
    )

    # Add the new field for product information
    products_in_basket = serializers.SerializerMethodField()

    class Meta:
        model = Basket
        fields = settings.BASKET_FIELDS  # Include the new field

    def get_products_in_basket(self, obj):
        """
        Custom method to retrieve product information from the basket.
        `obj` is the Basket instance being serialized.
        """
        products_data = {}

        # Iterate over all lines in the basket
        for line in obj.lines.all():  # Adjust this based on your actual model relationships
            product_id = str(line.product.id)  # Convert to string to match your JSON keys

            # Prepare the data for this line
            line_data = {
                "qty": line.quantity,
                "line_id": line.id,
                "attributes": self.get_attributes(line),  # Call helper method to get attributes
                "title": line.product.title,  # Add product title
                "original_price": line.product.original_price,  # Add product title
                "price_currency": line.product.price_currency,  # Add product title
                "selling_price": line.product.selling_price,  # Add product title
                "image": self.get_product_images(line.product),  # Add product images
            }

            # Append the line data to the product's list
            if product_id not in products_data:
                products_data[product_id] = []
            products_data[product_id].append(line_data)

        return products_data
    def get_product_images(self, product):
            """
            Helper method to retrieve product images using the `get_all_images` method.
            """
            images = []

            # Use the `get_all_images` method from the AbstractProduct model
            for image in product.get_all_images():
                images.append(image.original.url)  # Use the `original` field to get the image URL
                break
            if len(images)>0:
                return images[0]
            else:
                return ""
    def get_attributes(self, line):
        """
        Helper method to retrieve attributes for a line.
        This can return either a dictionary or a list of dictionaries.
        """
        # Example logic for attributes (adjust based on your actual model/data)
        attributes = []

        # Assuming `line.attributes` is a related field (e.g., ManyToMany or ForeignKey)
        for attr in line.attributes.all():
            attributes.append({
                "value": attr.value,
                "name": attr.option.name,
            })

        # Return as a dictionary if there's only one attribute, otherwise return a list
        return attributes
    

class BasketLineSerializer(OscarHyperlinkedModelSerializer):
    """
    This serializer computes the prices of this line by using the basket
    strategy.
    """

    url = DrillDownHyperlinkedIdentityField(
        view_name="basket-line-detail", extra_url_kwargs={"basket_pk": "basket.id"}
    )
    attributes = LineAttributeSerializer(
        many=True, fields=("id", "option", "value","price","type","name"), required=False, read_only=True
    )
    price_excl_tax = serializers.DecimalField(
        decimal_places=2,
        max_digits=12,
        source="line_price_excl_tax_incl_discounts",
        read_only=True,
    )
    price_incl_tax = TaxIncludedDecimalField(
        decimal_places=2,
        max_digits=12,
        excl_tax_field="line_price_excl_tax_incl_discounts",
        source="line_price_incl_tax_incl_discounts",
        read_only=True,
    )
    price_incl_tax_excl_discounts = TaxIncludedDecimalField(
        decimal_places=2,
        max_digits=12,
        excl_tax_field="line_price_excl_tax",
        source="line_price_incl_tax",
        read_only=True,
    )
    price_excl_tax_excl_discounts = serializers.DecimalField(
        decimal_places=2, max_digits=12, source="line_price_excl_tax", read_only=True
    )
    warning = serializers.CharField(
        read_only=True, required=False, source="get_warning"
    )
    options = OptionValueSerializer(many=True, required=False)

    stockrecord = DrillDownHyperlinkedRelatedField(
        view_name="product-stockrecord-detail",
        extra_url_kwargs={"product_pk": "product_id"},
        queryset=StockRecord.objects.all(),
    )

    class Meta:
        model = Line
        fields = settings.BASKETLINE_FIELDS

    def to_representation(self, instance):
        # This override is needed to reflect offer discounts or strategy
        # related prices immediately in the response
        operations.assign_basket_strategy(instance.basket, self.context["request"])

        # Oscar stores the calculated discount in line._discount_incl_tax or
        # line._discount_excl_tax when offers are applied. So by just
        # retrieving the line from the db you will loose this values, that's
        # why we need to get the line from the in-memory resultset here
        lines = (x for x in instance.basket.all_lines() if x.id == instance.id)
        line = next(lines, None)

        return super(BasketLineSerializer, self).to_representation(line)


class VoucherAddSerializer(serializers.Serializer):
    vouchercode = serializers.CharField(max_length=128, required=True)

    def validate(self, attrs):
        # oscar expects this always to be uppercase.
        attrs["vouchercode"] = attrs["vouchercode"].upper()

        request = self.context.get("request")
        try:
            voucher = Voucher.objects.get(code=attrs.get("vouchercode"))

            # check expiry date
            if not voucher.is_active():
                message = _("The '%(code)s' voucher has expired") % {
                    "code": voucher.code
                }
                raise serializers.ValidationError(message)

            # check voucher rules
            is_available, message = voucher.is_available_to_user(request.user)
            if not is_available:
                raise serializers.ValidationError(message)
        except Voucher.DoesNotExist:
            raise serializers.ValidationError(_("Voucher code unknown"))

        # set instance to the voucher so we can use this in the view
        self.instance = voucher
        return attrs

    def create(self, validated_data):
        return Voucher.objects.create(**validated_data)
