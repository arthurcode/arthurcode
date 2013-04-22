from django.db import models
from utils.validators import not_blank


class AbstractAddress(models.Model):
    """
    An abstract address class.  The name, first address line, and country fields are required.
    Most addresses probably do require a postal code, but I believe there are some international ones that
    don't.  Similarly the region may not always be required.
    """

    name = models.CharField(max_length=100, verbose_name="Addressee", validators=[not_blank])
    line1 = models.CharField(max_length=200, verbose_name="Address Line 1", validators=[not_blank])
    line2 = models.CharField(max_length=200, verbose_name="Address Line 2", null=True, blank=True)
    country = models.CharField(max_length=50, validators=[not_blank])
    post_code = models.CharField(max_length=20, verbose_name="Zip/Postal Code", null=True, blank=True)
    region = models.CharField(max_length=50, verbose_name="Province/State", null=True, blank=True)

    class Meta:
        abstract = True
