from django.db import models
from utils.validators import not_blank
from django_countries import CountryField
from arthurcode import settings
from comments.akismet import comment_check, AkismetError, verify_key, submit_spam, submit_ham
from django.contrib.sites.models import Site
from utils.util import get_full_url


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

    def as_dict(self):
        return {
            'name': self.name,
            'phone': self.phone,
            'line1': self.line1,
            'line2': self.line2,
            'city': self.city,
            'region': self.region,
            'country': self.country,
            'post_code': self.post_code,
            'address_id': self.id,             #TODO: change this to 'id' instead
        }


class AkismetMixin(object):
    """
    Adds spam-checking functionality to an object.
    """

    def get_spam_data(self, request=None):
        """
        Returns the data dict that will be used to determine whether or not this object is SPAM.  Subclasses should
        override this method and augment the dictionary with model-specific fields.
        """
        data = {}
        data['permalink'] = get_full_url(self, request) # request may be None
        if request:
            data['referrer'] = request.META.get('HTTP_REFERER', '')
            data['user_agent'] = request.META.get('HTTP_USER_AGENT', '')
            data['user_ip'] = request.META.get("REMOTE_ADDR", '')
        return data

    def check_spam(self, request=None):
        """
        Returns True if the comment is spam and False if it's ham.
        """
        key = self._get_key()

        if not key:
            # TODO: log a warning
            return False

        domain = self._get_domain()

        try:
            if verify_key(key, domain):
                data = self.get_spam_data(request)
                return comment_check(key, domain, **data)
        except AkismetError, e:
            # TODO: log a warning with the exception
            print e.response, e.statuscode
        return False

    def marked_as_spam(self):
        key = self._get_key()
        if not key:
            return

        domain = self._get_domain()
        try:
            if verify_key(key, domain):
                data = self.get_spam_data()
                submit_spam(key, domain, **data)
        except AkismetError, e:
            print e.response, e.statuscode

    def marked_not_spam(self):
        key = self._get_key()
        if not key:
            return

        domain = self._get_domain()
        try:
            if verify_key(key, domain):
                data = self.get_spam_data()
                submit_ham(key, domain, **data)
        except AkismetError, e:
            print e.response, e.statuscode

    def _get_key(self):
        return getattr(settings, 'AKISMET_KEY', None)

    def _get_domain(self):
        return Site.objects.get_current().domain



