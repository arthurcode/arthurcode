from django.db import models
from utils.validators import not_blank
from django_countries import CountryField



class AbstractAddress(models.Model):
    """
    An abstract address class.  The name, first address line, and country fields are required.
    Most addresses probably do require a postal code, but I believe there are some international ones that
    don't.  Similarly the region may not always be required.
    """

    PHONE_NUMBER_LENGTH = 20
    ADDRESSEE_LENGTH = 100
    LINE_LENGTH = 200
    CITY_LENGTH = 50
    REGION_LENGTH = 50
    POST_CODE_LENGTH = 20

    name = models.CharField(max_length=ADDRESSEE_LENGTH, verbose_name="Addressee", validators=[not_blank])
    line1 = models.CharField(max_length=LINE_LENGTH, verbose_name="Address Line 1", validators=[not_blank])
    line2 = models.CharField(max_length=LINE_LENGTH, verbose_name="Address Line 2", null=True, blank=True)
    city = models.CharField(max_length=CITY_LENGTH, verbose_name="City/Town", null=True, blank=True)
    region = models.CharField(max_length=REGION_LENGTH, verbose_name="Province/State", null=True, blank=True)
    country = CountryField()
    post_code = models.CharField(max_length=POST_CODE_LENGTH, verbose_name="Zip/Postal Code", null=True, blank=True)
    phone_number = models.CharField(max_length=PHONE_NUMBER_LENGTH, null=True, blank=True)

    class Meta:
        abstract = True
