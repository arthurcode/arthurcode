from lazysignup.decorators import allow_lazy_user
from django.core.urlresolvers import reverse_lazy, reverse
from django.http import HttpResponseRedirect
from checkout.forms import ContactInfoForm, PaymentInfoForm
from utils.forms import CanadaShippingForm, BillingForm
from django.shortcuts import render_to_response
from django.template import RequestContext
from cart import cartutils


class Step:

    def __init__(self, checkout):
        self.checkout = checkout

    @property
    def request(self):
        return self.checkout.request

    def process(self):
        if self.request.method == "POST":
            return self._post()
        return self._get()

    def mark_complete(self):
        self.checkout._mark_step_complete(self)

    def _get(self):
        raise Exception("Subclasses must override the _get method.")

    def _post(self):
        raise Exception("Subclasses must override the _post method.")


class ContactInfoStep(Step):

    def _get(self):
        form = ContactInfoForm()
        return self._render_form(form)

    def _render_form(self, form):
        context = {
            'form': form
        }
        return render_to_response('contact_info.html', context, context_instance=RequestContext(self.request))

    def _post(self):
        data = self.request.POST.copy()
        form = ContactInfoForm(data)
        if form.is_valid():
            self.checkout._mark_step_complete(self)
            return HttpResponseRedirect(self.checkout.get_next_url())
        return self._render_form(form)


class ShippingInfoStep(Step):

    def _get(self):
        form = CanadaShippingForm()
        return self._render_form(form)

    def _render_form(self, form):
        context = {
            'form': form
        }
        return render_to_response('shipping_form.html', context, context_instance=RequestContext(self.request))

    def _post(self):
        data = self.request.POST.copy()
        form = CanadaShippingForm(data)
        if form.is_valid():
            self.checkout._mark_step_complete(self)
            return HttpResponseRedirect(self.checkout.get_next_url())
        return self._render_form(form)


class BillingInfoStep(Step):

    def _get(self):
        form = BillingForm()
        return self._render_form(form)

    def _render_form(self, form):
        context = {
            'form': form
        }
        return render_to_response('billing_form.html', context, context_instance=RequestContext(self.request))

    def _post(self):
        data = self.request.POST.copy()
        form = BillingForm(data)
        if form.is_valid():
            self.checkout._mark_step_complete(self)
            return HttpResponseRedirect(self.checkout.get_next_url())
        return self._render_form(form)


class ReviewStep(Step):
    def _get(self):
        form = PaymentInfoForm()
        return self._render_form(form)

    def _render_form(self, form):
        context = {
            'form': form
        }
        return render_to_response('review_and_pay.html', context, context_instance=RequestContext(self.request))

    def _post(self):
        data = self.request.POST.copy()
        form = PaymentInfoForm(data)
        if form.is_valid():
            self.checkout._mark_step_complete(self)
            return HttpResponseRedirect(self.checkout.get_next_url())
        return self._render_form(form)


class Checkout:

    DATA_KEY = 'checkout'

    def __init__(self, request):
        self.request = request

    def start(self):
        """
        The user has visited the root checkout url.  Initialize a checkout data dictionary.
        """
        data = self._get_data()

        if not data:
            self._save_data({})

        if self.is_finished():
            # start a new checkout process
            self._save_data({})

    def is_started(self):
        return self._get_data() != None

    def is_finished(self):
        return self.get_completed_step() == len(STEPS)

    def get_completed_step(self):
        """
        Returns the highest step that this user has completed, or None if no steps have been completed.
        """
        return self.get('step', None)

    def get_step_number(self, step):
        if isinstance(step, Step):
            for i in range(len(STEPS)):
                step_clazz = STEPS[i][0]
                if step.__class__ == step_clazz:
                    return i + 1
        # assume we were given an integer
        return int(step)

    def _mark_step_complete(self, step):
        # only store the highest completed step
        step_num = self.get_step_number(step)

        if step_num > self.get_completed_step():
            self.save('step', step_num)

    def process_step(self, step):
        if not self.is_started():
            # redirect user to the 'starting' checkout url
            return HttpResponseRedirect(reverse('checkout'))

        highest_completed_step = self.get_completed_step() or 0
        if step > highest_completed_step + 1:
            # the user is not allowed to skip ahead like this.  Redirect them to the proper step
            return HttpResponseRedirect(self.get_next_url())

        if not cartutils.cart_distinct_item_count(self.request):
            # there are no items in the customer's cart!  Redirect them to the cart page
            return HttpResponseRedirect(reverse('show_cart'))

        clazz, url = STEPS[step-1]
        return clazz(self).process()

    def get_next_url(self):
        step = self.get_completed_step() or 0
        next_step = step + 1
        if next_step <= len(STEPS):
            _, url = STEPS[next_step-1]
            return url
        # the step is outside of our expected url range.  We must be finished the checkout process
        # for now just return a dummy url
        return reverse('show_account')

    def save(self, key, value):
        data = self._get_data()
        data[key] = value
        self._save_data(data)

    def get(self, key, default=None):
        data = self._get_data()
        return data.get(key, default)

    def _save_data(self, data):
        checkout_data = data or {}
        # make sure this saves to the DB
        self.request.session[Checkout.DATA_KEY] = checkout_data

    def _get_data(self):
        """
        Returns the checkout data associated with this session.  Wil return None if there is no checkout data stored.
        """
        return self.request.session.get(Checkout.DATA_KEY, None)

    def _clear_data(self):
        """
        Removes all data associated with this checkout session.  This should be called after a user completes the
        checkout process.
        """
        if Checkout.DATA_KEY in self.request.session:
            del self.request.session[Checkout.DATA_KEY]


# defines the step ordering and the associated step url or the entire checkout process
STEPS = [(ContactInfoStep, reverse_lazy('contact')),
         (ShippingInfoStep, reverse_lazy('shipping')),
         (BillingInfoStep, reverse_lazy('billing')),
         (ReviewStep, reverse_lazy('review'))]


@allow_lazy_user
def checkout(request):
    """
    Checkout a logged-in user.
    """
    co = Checkout(request)
    co.start()
    # re-direct the user to the next applicable step in their checkout process.  This will always be the first step
    # for new checkouts.
    return HttpResponseRedirect(co.get_next_url())


def contact_info(request):
    """
    Gather or confirm the user's contact information
    """
    co = Checkout(request)
    return co.process_step(1)


def shipping_info(request):
    """
    Gather or confirm the user's shipping information
    """
    co = Checkout(request)
    return co.process_step(2)


def billing_info(request):
    """
    Gather or confirm the user's billing information
    """
    co = Checkout(request)
    return co.process_step(3)


def review(request):
    """
    Ask the customer to review their order & pay.
    """
    co = Checkout(request)
    return co.process_step(4)