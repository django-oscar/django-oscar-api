from oscarapi.apps.basket.abstract_models import AbstractBasket, AbstractLine
from oscar.core.loading import is_model_registered


if not is_model_registered('basket', 'Basket'):
    class Basket(AbstractBasket):
        pass

if not is_model_registered('basket', 'Line'):
    class Line(AbstractLine):
        pass

from oscar.apps.basket.models import LineAttribute  # noqa
