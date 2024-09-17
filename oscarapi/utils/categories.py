from django.utils.translation import gettext as _
from django.db import transaction

from rest_framework.exceptions import NotFound

from oscar.core.loading import get_model

Category = get_model("catalogue", "category")


def create_from_sequence(bits, create):
    """
    Create categories from an iterable
    """
    if len(bits) == 1:
        # Get or create root node
        slug = bits[0]
        try:
            # Category names should be unique at the depth=1
            root = Category.objects.get(depth=1, slug=slug)
        except Category.DoesNotExist:
            if create:
                root = Category.add_root(name=slug, slug=slug)
            else:
                raise NotFound(
                    _("No %(verbose_name)s found matching the query")
                    % {"verbose_name": Category._meta.verbose_name}
                )
        except Category.MultipleObjectsReturned:
            raise ValueError(
                "There are more than one categories with slug " "%s at depth=1" % slug
            )
        return [root]
    else:
        parents = create_from_sequence(bits[:-1], create)
        parent, slug = parents[-1], bits[-1]
        try:
            child = parent.get_children().get(slug=slug)
        except Category.DoesNotExist:
            if create:
                child = parent.add_child(name=slug, slug=slug)
            else:
                raise NotFound(
                    _("No %(verbose_name)s found matching the query")
                    % {"verbose_name": Category._meta.verbose_name}
                )
        except Category.MultipleObjectsReturned:
            raise ValueError(
                (
                    "There are more than one categories with slug "
                    "%s which are children of %s"
                )
                % (slug, parent)
            )
        parents.append(child)
        return parents


def create_from_full_slug(breadcrumb_str, separator="/"):
    """
    Create categories from a breadcrumb string
    """
    category_names = [x.strip() for x in breadcrumb_str.split(separator)]
    categories = create_from_sequence(category_names, True)
    return categories[-1]


def find_from_full_slug(breadcrumb_str, separator="/"):
    """
    Find categories from a breadcrumb string
    """
    category_names = [x.strip() for x in breadcrumb_str.split(separator)]
    categories = create_from_sequence(category_names, False)
    return categories[-1]


def upsert_categories(data):
    with transaction.atomic():
        categories_to_update, fields_to_update = _upsert_categories(data)

        if categories_to_update and fields_to_update:
            Category.objects.bulk_update(categories_to_update, fields_to_update)

        Category.fix_tree()


def _upsert_categories(data, parent_category=None):
    if parent_category is None:
        # Get the last category in the root
        sibling = Category.get_last_root_node()
    else:
        # Set sibling to None if there is a parent category, we want the first category in the data to be added as a first-child of the parent
        sibling = None

    categories_to_update = []
    category_fields_to_update = set()

    for cat in data:
        children = cat.pop("children", None)

        try:
            category = Category.objects.get(code=cat["data"]["code"])

            for key, value in cat["data"].items():
                setattr(category, key, value)
                category_fields_to_update.add(key)

            categories_to_update.append(category)
        except Category.DoesNotExist:
            # Category with code does not exist, create it on the root or under the parent
            if parent_category:
                category = parent_category.add_child(**cat["data"])
            else:
                category = Category.add_root(**cat["data"])

        if sibling is not None:
            if category.pk != sibling.pk:
                # Move the category to the right of the sibling
                category.move(sibling, pos="right")
        elif parent_category is not None:
            get_parent = category.get_parent()
            if (get_parent is None and parent_category is not None) or (
                get_parent.pk != parent_category.pk
            ):
                # Move the category as the first child under the parent category since we have no sibling
                category.move(parent_category, pos="first-child")

        # Update the new path from the database after moving the category to it's new home
        category.refresh_from_db(fields=["path"])

        # The category is now the sibling, new categories will be moved to the right of this category
        sibling = category

        if children:
            # Add children under this category
            _categories_to_update, _category_fields_to_update = _upsert_categories(
                children, parent_category=category
            )
            categories_to_update.extend(_categories_to_update)
            if _category_fields_to_update:
                category_fields_to_update.update(_category_fields_to_update)

    return categories_to_update, category_fields_to_update
