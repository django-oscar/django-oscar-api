from commerceconnect.apps.basket.abstract_models import AbstractBasket
from oscar.core.loading import is_model_registered


if not is_model_registered('basket', 'Basket'):
    class Basket(AbstractBasket):
        pass

from oscar.apps.basket.models import Line, LineAttribute #noqa
