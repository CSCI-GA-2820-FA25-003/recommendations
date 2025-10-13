"""
Test Factory to make fake objects for testing
"""

import random
from datetime import datetime, timezone
from decimal import Decimal

import factory
from service.models import Recommendation


def _fake_confidence() -> Decimal:
    return Decimal(str(round(random.uniform(0, 1), 2)))
    # return Decimal(random.randrange(-99, 100)) / Decimal(100)


class RecommendationFactory(factory.Factory):
    """Creates fake recommendations"""

    class Meta:  # pylint: disable=too-few-public-methods
        """Maps factory to data model"""

        model = Recommendation

    id = factory.Sequence(lambda n: n + 1)
    base_product_id = factory.Sequence(lambda n: n + 100)
    recommended_product_id = factory.Sequence(lambda n: n + 200)
    recommendation_type = factory.Iterator(["cross-sell", "up-sell", "accessory"])
    status = factory.Iterator(["active", "inactive"])

    confidence_score = factory.LazyFunction(_fake_confidence)
    base_product_price = factory.Faker(
        "pydecimal", left_digits=4, right_digits=2, positive=True
    )
    recommended_product_price = factory.Faker(
        "pydecimal", left_digits=4, right_digits=2, positive=True
    )

    base_product_description = factory.Faker("sentence", nb_words=6)
    recommended_product_description = factory.Faker("sentence", nb_words=6)

    created_date = factory.LazyFunction(lambda: datetime.now(timezone.utc))
    updated_date = factory.LazyFunction(lambda: datetime.now(timezone.utc))
