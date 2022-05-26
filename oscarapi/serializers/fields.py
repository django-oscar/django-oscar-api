import logging
import operator
import shutil
import tempfile

from os.path import basename, join, splitext
from urllib.parse import urlsplit, parse_qs
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from django.conf import settings
from django.db import IntegrityError
from django.utils.translation import ugettext as _
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.files import File
from django.utils.functional import cached_property
from rest_framework import serializers, relations
from rest_framework.fields import get_attribute

from oscar.core.loading import get_model, get_class

from oscarapi import version
from oscarapi.utils.loading import get_api_class
from oscarapi.utils.exists import bound_unique_together_get_or_create
from oscarapi.utils.settings import overridable
from .exceptions import FieldError

logger = logging.getLogger(__name__)
ProductAttribute = get_model("catalogue", "ProductAttribute")
Category = get_model("catalogue", "Category")
create_from_breadcrumbs = get_class("catalogue.categories", "create_from_breadcrumbs")
entity_internal_value = get_api_class("serializers.hooks", "entity_internal_value")
attribute_details = operator.itemgetter("code", "value")


class TaxIncludedDecimalField(serializers.DecimalField):
    def __init__(self, excl_tax_field=None, excl_tax_value=None, **kwargs):
        self.excl_tax_field = excl_tax_field
        self.excl_tax_value = excl_tax_value
        super(TaxIncludedDecimalField, self).__init__(**kwargs)

    def get_attribute(self, instance):
        if instance.is_tax_known:
            return super(TaxIncludedDecimalField, self).get_attribute(instance)
        if self.excl_tax_field:
            return get_attribute(instance, (self.excl_tax_field,))
        return self.excl_tax_value


class DrillDownHyperlinkedMixin:
    def __init__(self, *args, **kwargs):
        try:
            self.extra_url_kwargs = kwargs.pop("extra_url_kwargs")
        except KeyError:
            msg = "DrillDownHyperlink Fields require an 'extra_url_kwargs' argument"
            raise ValueError(msg)

        super().__init__(*args, **kwargs)

    def get_extra_url_kwargs(self, obj):
        return {
            key: operator.attrgetter(path)(obj)
            for key, path in self.extra_url_kwargs.items()
        }

    def get_url(
        self, obj, view_name, request, format
    ):  # pylint: disable=redefined-builtin
        """
        Given an object, return the URL that hyperlinks to the object.

        May raise a `NoReverseMatch` if the `view_name` and `lookup_field`
        attributes are not configured to correctly match the URL conf.
        """
        if hasattr(obj, "pk") and obj.pk in (None, ""):
            return None

        lookup_value = getattr(obj, self.lookup_field)
        kwargs = {self.lookup_url_kwarg: lookup_value}
        kwargs.update(self.get_extra_url_kwargs(obj))
        return self.reverse(view_name, kwargs=kwargs, request=request, format=format)


class DrillDownHyperlinkedIdentityField(
    DrillDownHyperlinkedMixin, relations.HyperlinkedIdentityField
):
    pass


class DrillDownHyperlinkedRelatedField(
    DrillDownHyperlinkedMixin, relations.HyperlinkedRelatedField
):
    def use_pk_only_optimization(self):
        # we always want the full object so the mixin can filter on the attributes
        # specified with get_extra_url_kwargs
        return False


class AttributeValueField(serializers.Field):
    """
    This field is used to handle the value of the ProductAttributeValue model

    Because the value is dependant on the type of the corresponding attribute,
    it is not fixed. This field solves the problem of handling the different
    types.
    """

    def __init__(self, **kwargs):
        # this field always needs the full object
        kwargs["source"] = "*"
        kwargs["error_messages"] = {
            "no_such_option": _("{code}: Option {value} does not exist."),
            "invalid": _("Wrong type, {error}."),
            "attribute_validation_error": _(
                "Error assigning `{value}` to {code}, {error}."
            ),
            "attribute_required": _("Attribute {code} is required."),
            "attribute_missing": _(
                "No attribute exist with code={code}, "
                "please define it in the product_class first."
            ),
            "child_without_parent": _(
                "Can not find attribute if product_class is empty and "
                "parent is empty as well, child without parent?"
            ),
        }
        super(AttributeValueField, self).__init__(**kwargs)

    def get_value(self, dictionary):
        # return all the data because this field uses everything
        return dictionary

    def to_internal_value(self, data):  # noqa
        assert "product" in data or "product_class" in data or "parent" in data

        try:
            code, value = attribute_details(data)
            internal_value = value

            if "product" in data:
                # we need the attribute to determine the type of the value
                attribute = ProductAttribute.objects.get(
                    code=code, product_class__products__id=data["product"]
                )
            elif "product_class" in data and data["product_class"] is not None:
                attribute = ProductAttribute.objects.get(
                    code=code, product_class__slug=data.get("product_class")
                )
            elif "parent" in data:
                attribute = ProductAttribute.objects.get(
                    code=code, product_class__products__id=data["parent"]
                )

            if attribute.required and value is None:
                self.fail("attribute_required", code=code)

            # some of these attribute types need special processing, or their
            # validation will fail
            if attribute.type == attribute.OPTION:
                internal_value = attribute.option_group.options.get(option=value)
            elif attribute.type == attribute.MULTI_OPTION:
                if attribute.required and not value:
                    self.fail("attribute_required", code=code)
                internal_value = attribute.option_group.options.filter(option__in=value)
                if len(value) != internal_value.count():
                    non_existing = set(value) - set(
                        internal_value.values_list("option", flat=True)
                    )
                    non_existing_as_error = ",".join(sorted(non_existing))
                    self.fail("no_such_option", value=non_existing_as_error, code=code)
            elif attribute.type == attribute.DATE:
                date_field = serializers.DateField()
                internal_value = date_field.to_internal_value(value)
            elif attribute.type == attribute.DATETIME:
                date_field = serializers.DateTimeField()
                internal_value = date_field.to_internal_value(value)
            elif attribute.type == attribute.ENTITY:
                internal_value = entity_internal_value(attribute, value)

            # the rest of the attribute types don't need special processing
            try:
                attribute.validate_value(internal_value)
            except TypeError as e:
                self.fail(
                    "attribute_validation_error",
                    code=code,
                    value=internal_value,
                    error=e,
                )
            except ValidationError as e:
                self.fail(
                    "attribute_validation_error",
                    code=code,
                    value=internal_value,
                    error=",".join(e.messages),
                )

            return {"value": internal_value, "attribute": attribute}
        except ProductAttribute.DoesNotExist:
            if (
                "product_class" in data
                and "parent" in data
                and data["product_class"] is None
                and data["parent"] is None
            ):
                self.fail("child_without_parent")
            else:
                self.fail("attribute_missing", **data)
        except ObjectDoesNotExist:
            self.fail("no_such_option", value=value, code=code)
        except KeyError as e:
            (field_name,) = e.args
            raise FieldError(
                detail={field_name: self.error_messages["required"]}, code="required"
            )

    def to_representation(self, value):
        obj_type = value.attribute.type
        if obj_type == value.attribute.OPTION:
            return value.value.option
        elif obj_type == value.attribute.MULTI_OPTION:
            return value.value.values_list("option", flat=True)
        elif obj_type == value.attribute.FILE:
            return value.value.url
        elif obj_type == value.attribute.IMAGE:
            return value.value.url
        elif obj_type == value.attribute.ENTITY:
            if hasattr(value.value, "json"):
                return value.value.json()
            else:
                return _(
                    "%(entity)s has no json method, can not convert to json"
                    % {"entity": repr(value.value)}
                )

        # return the value as stored on ProductAttributeValue in the correct type
        return value.value


class CategoryField(serializers.RelatedField):
    def __init__(self, **kwargs):
        kwargs["queryset"] = Category.objects
        super(CategoryField, self).__init__(**kwargs)

    def to_internal_value(self, data):
        return create_from_breadcrumbs(data)

    def to_representation(self, value):
        return value.full_name


class SingleValueSlugRelatedField(serializers.SlugRelatedField):
    """
    Represents a queryset as a list of slugs, and can be used to create new
    items, as long as only the slug_field is required
    """

    def get_bound_queryset(self):
        parent = self.parent
        source_name = parent.source
        if hasattr(parent, "child_relation"):
            parent = parent.parent

        return getattr(parent.instance, source_name, None)

    def to_internal_value(self, data):
        qs = self.get_bound_queryset()
        if qs is not None:  # first try to obtain a bound item.
            try:
                return bound_unique_together_get_or_create(qs, {self.slug_field: data})
            except IntegrityError:
                pass

        # if no bound item can be found, return an unbound unsaved instance.
        qs = self.get_queryset()
        return {self.slug_field: data}


class LazyRemoteFile(File):
    """
    This file will defer downloading untill the file data is accessed.

    It will also try to parsed a sha1 hash from the url, and store it as an
    attribute, so the file_hash function will use it. You can use this feature
    to avoid unnescessary downloading of files. Just compute the hash on the
    client side and send it along in the url like this::

        http://example.com/image.jpg?sha1=751499a82438277cb3cfb5db268bd41696739b3b

    It will only download if not allready available locally.
    """

    def __init__(self, url, name=None, mode="rb"):
        parsed_url = urlsplit(url)
        self.mode = mode
        self.name = name
        self.size = 1
        self.url = url

        # compute a hash if available
        sha1_hash = next(iter(parse_qs(parsed_url.query).get("sha1", [])), None)
        if sha1_hash:
            self.sha1 = sha1_hash

    def read(self, size=-1):
        try:
            return self.file.read(size)
        except HTTPError as e:
            raise serializers.ValidationError(
                "Error when downloading image %s, %s: %s" % (self.url, e.code, e.reason)
            )

    @cached_property
    def file(self):
        headers = overridable(
            "OSCARAPI_LAZY_REMOTE_FILE_REQUEST_HEADERS",
            default={"User-Agent": f"django-oscar-api/{version}"},
        )
        request = Request(self.url, headers=headers)

        _, ext = splitext(self.name)

        # Try to keep file in memory, but do not exceed FILE_UPLOAD_MAX_MEMORY_SIZE
        result_file = tempfile.SpooledTemporaryFile(
            max_size=settings.FILE_UPLOAD_MAX_MEMORY_SIZE,
            mode="wb",
            suffix=".upload" + ext,
            dir=settings.FILE_UPLOAD_TEMP_DIR,
        )
        response = urlopen(request)
        # copy the response into a file so it can be read multiple times
        shutil.copyfileobj(response, result_file)

        result_file.seek(0)
        return result_file

    def __str__(self):
        return self.url or ""

    def __bool__(self):
        return bool(self.url)

    def open(self, mode="rb"):
        if not self.closed:
            self.seek(0)

        return self


class ImageUrlField(serializers.ImageField):
    def __init__(self, **kwargs):
        super(ImageUrlField, self).__init__(**kwargs)
        self.use_url = True

    def to_internal_value(self, data):
        http_prefix = data.startswith(("http:", "https:"))
        if http_prefix:
            request = self.context.get("request", None)
            if request:  # if there is a request, we can get the hostname from that
                parsed_url = urlsplit(data)
                host = request.get_host()
                if (
                    host != parsed_url.netloc
                ):  # we are only downloading files from a foreign server
                    # download only when needed
                    return LazyRemoteFile(data, name=basename(parsed_url.path))
                else:
                    location = parsed_url.path
                    path = join(
                        settings.MEDIA_ROOT, location.replace(settings.MEDIA_URL, "", 1)
                    )
                    file_object = File(open(path, "rb"), name=basename(parsed_url.path))

                return super(ImageUrlField, self).to_internal_value(file_object)

        return super(ImageUrlField, self).to_internal_value(data)
