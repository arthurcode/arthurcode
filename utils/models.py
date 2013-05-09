from django.db import models
from utils.validators import not_blank
from django_countries import CountryField


class AbstractAddress(models.Model):
    """
    An abstract address class.  The first address line, city, region and country fields are required.
    Most addresses probably do require a postal code, but I believe there are some international ones that
    don't.  I've modelled this class on the PayPal gateway address objects in which the same fields are required.
    I've also used PayPal's max character lengths to decide on the max field lengths below.
    https://developer.paypal.com/webapps/developer/docs/api/
    """

    PHONE_NUMBER_LENGTH = 50
    ADDRESSEE_LENGTH = 50
    LINE_LENGTH = 100
    CITY_LENGTH = 50
    REGION_LENGTH = 100
    POST_CODE_LENGTH = 20

    name = models.CharField(max_length=ADDRESSEE_LENGTH, verbose_name="Addressee", null=True, blank=True)
    line1 = models.CharField(max_length=LINE_LENGTH, verbose_name="Address Line 1", validators=[not_blank])
    line2 = models.CharField(max_length=LINE_LENGTH, verbose_name="Address Line 2", null=True, blank=True)
    city = models.CharField(max_length=CITY_LENGTH, verbose_name="City/Town", validators=[not_blank])
    region = models.CharField(max_length=REGION_LENGTH, verbose_name="Province/State", validators=[not_blank])
    country = CountryField()
    post_code = models.CharField(max_length=POST_CODE_LENGTH, verbose_name="Zip/Postal Code", null=True, blank=True)
    phone = models.CharField(max_length=PHONE_NUMBER_LENGTH, null=True, blank=True)

    class Meta:
        abstract = True

    def as_address(self, base_clazz):
        """
        Copies the common fields from this Address class to a different Address class.
        """
        address = base_clazz()
        address.name = self.name
        address.line1 = self.line1
        address.line2 = self.line2
        address.city = self.city
        address.region = self.region
        address.country = self.country
        address.post_code = self.post_code
        address.phone = self.phone
        return address

    def __unicode__(self):
        fields = [
            self.name or "-",
            self.phone or "-",
            self.line1 or "-",
            self.line2 or "-",
            self.city or "-",
            self.region or "-",
            self.post_code or "-",
            unicode(self.country),
        ]
        return " ".join(fields)