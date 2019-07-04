from oscar.core.loading import get_model

Category = get_model('catalogue', 'category')


def create_from_sequence(bits):
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
            root = Category.add_root(name=slug, slug=slug)
        except Category.MultipleObjectsReturned:
            raise ValueError((
                "There are more than one categories with slug "
                "%s at depth=1") % slug)
        return [root]
    else:
        parents = create_from_sequence(bits[:-1])
        parent, slug = parents[-1], bits[-1]
        try:
            child = parent.get_children().get(slug=slug)
        except Category.DoesNotExist:
            child = parent.add_child(name=slug, slug=slug)
        except Category.MultipleObjectsReturned:
            raise ValueError((
                "There are more than one categories with slug "
                "%s which are children of %s") % (slug, parent))
        parents.append(child)
        return parents


def create_from_full_slug(breadcrumb_str, separator='/'):
    """
    Create categories from a breadcrumb string
    """
    category_names = [x.strip() for x in breadcrumb_str.split(separator)]
    categories = create_from_sequence(category_names)
    return categories[-1]
