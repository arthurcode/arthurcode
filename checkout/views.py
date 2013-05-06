from lazysignup.decorators import allow_lazy_user
from lazysignup.utils import is_lazy_user
from django.core.urlresolvers import reverse_lazy, reverse
from django.http import HttpResponseRedirect
from checkout.forms import ContactInfoForm, PaymentInfoForm
from utils.forms import CanadaShippingForm, BillingForm
from django.shortcuts import render_to_response
from django.template import RequestContext
from cart import cartutils
from orders.models import Order, OrderShippingAddress, OrderBillingAddress, OrderItem
import decimal
from utils.util import round_cents
from accounts.models import CustomerProfile
from utils.validators import is_blank


class Step:

    data_key = 'step'

    def __init__(self, checkout):
        self.checkout = checkout
        data = self._get_data()
        if not data:
            self.checkout.save(self.data_key, {})

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

    def _get_data(self):
        return self.checkout.get(self.data_key, None)

    def save(self, key, value):
        data = self._get_data()
        data[key] = value
        self.request.session.modified = True

    def get(self, key, default=None):
        return self._get_data().get(key, default)


class ContactInfoStep(Step):

    data_key = 'contact'
    form_key = 'contact_form'

    def _get(self):
        form = self.get_saved_form()
        if not form.is_bound:
            # there was no saved data, this is the first time the user is seeing this form.
            data = self.get_existing_contact_info()
            test_form = ContactInfoForm(data=data)
            if test_form.is_valid():
                # we have all of the information we need, we just need the user to validate it.
                return self._render_form(test_form, template='verify_contact_info.html')
            else:
                # we are missing some or all of the necessary data.  Render the Guest form, pre-filled with the data
                # values we already have.
                form = ContactInfoForm(initial=data)
        return self._render_form(form)

    def _render_form(self, form, template='contact_info.html'):
        context = {
            'form': form
        }
        if self.checkout.extra_context:
            context.update(self.checkout.extra_context)
        return render_to_response(template, context, context_instance=RequestContext(self.request))

    def _post(self):
        data = self.request.POST.copy()
        form = ContactInfoForm(data)
        if form.is_valid():
            self.save(self.form_key, self.request.POST.copy())
            self.checkout._mark_step_complete(self)
            self._save_form_data_to_profile(form)
            return HttpResponseRedirect(self.checkout.get_next_url())
        return self._render_form(form)

    def get_saved_form(self):
        saved_data = self.get(self.form_key, None)
        return ContactInfoForm(data=saved_data)

    def get_existing_contact_info(self):
        """
        Gets any existing contact info data that is stored in either the User object or the Customer Profile object.
        """
        data = {}
        user = self.checkout.get_user()
        if user:
            profile = self.checkout.get_customer_profile()
            self._add_to_data('first_name', user.first_name, data)
            self._add_to_data('last_name', user.last_name, data)
            self._add_to_data('email', user.email, data)
            self._add_to_data('email2', user.email, data)
            if profile:
                self._add_to_data('phone', profile.phone_number, data)
                self._add_to_data('contact_method', profile.contact_method, data)
        return data

    def _add_to_data(self, key, value, data):
        if not is_blank(value):
            data[key] = value

    def _save_form_data_to_profile(self, form):
        user = self.checkout.get_user()
        if not user:
            return
        cd = form.cleaned_data
        user.email = cd['email']
        user.first_name = cd['first_name']
        user.last_name = cd['last_name']
        user.save()

        profile = self.checkout.get_customer_profile()
        if not profile:
            profile = CustomerProfile(user=user)
        profile.contact_method = cd['contact_method']
        if 'phone' in cd:
            profile.phone_number = cd['phone']
        profile.save()


class ShippingInfoStep(Step):

    data_key = 'shipping'
    form_key = 'shipping_form'

    def _get(self):
        saved_data = self.get(self.form_key, None)
        form = CanadaShippingForm(data=saved_data)
        return self._render_form(form)

    def _render_form(self, form):
        context = {
            'form': form
        }
        if self.checkout.extra_context:
            context.update(self.checkout.extra_context)
        return render_to_response('shipping_form.html', context, context_instance=RequestContext(self.request))

    def _post(self):
        data = self.request.POST.copy()
        form = CanadaShippingForm(data)
        if form.is_valid():
            self.save(self.form_key, self.request.POST.copy())
            self.checkout._mark_step_complete(self)
            return HttpResponseRedirect(self.checkout.get_next_url())
        return self._render_form(form)

    def get_saved_form(self):
        saved_data = self.get(self.form_key, None)
        return CanadaShippingForm(data=saved_data)


class BillingInfoStep(Step):

    data_key = 'billing'
    form_key = 'billing_form'

    def _get(self):
        saved_data = self.get(self.form_key, None)
        form = BillingForm(data=saved_data)
        return self._render_form(form)

    def _render_form(self, form):
        context = {
            'form': form
        }
        if self.checkout.extra_context:
            context.update(self.checkout.extra_context)
        return render_to_response('billing_form.html', context, context_instance=RequestContext(self.request))

    def _post(self):
        data = self.request.POST.copy()
        form = BillingForm(data)
        if form.is_valid():
            self.save(self.form_key, self.request.POST.copy())
            self.checkout._mark_step_complete(self)
            return HttpResponseRedirect(self.checkout.get_next_url())
        return self._render_form(form)

    def get_saved_form(self):
        saved_data = self.get(self.form_key, None)
        return BillingForm(data=saved_data)


class ReviewStep(Step):

    data_key = 'review'

    def _get(self):
        form = PaymentInfoForm()
        return self._render_form(form)

    def _render_form(self, form):
        order, shipping_address, billing_address, order_items = self.checkout._build_order()
        if not form.is_bound:
            form.fields['total'].initial = order.total

        context = {
            'form': form,
            'order': order,
            'shipping_address': shipping_address,
            'billing_address': billing_address,
            'order_items': order_items,
        }
        if self.checkout.extra_context:
            context.update(self.checkout.extra_context)
        return render_to_response('review_and_pay.html', context, context_instance=RequestContext(self.request))

    def _post(self):
        data = self.request.POST.copy()
        form = PaymentInfoForm(data)
        if form.is_valid():
            success = self.checkout.process_order(form)
            if success:
                self.checkout._mark_step_complete(self)
                return HttpResponseRedirect(self.checkout.get_next_url())
        return self._render_form(form)


class Checkout:

    DATA_KEY = 'checkout'
    extra_context = {}

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

    def cancel(self):
        """
        Cancels any in-progress checkout steps
        """
        self._clear_data()

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

        self.extra_context = {
            'steps': STEPS,
            'current_step': step,
            'completed_step': highest_completed_step,
            'current_step_name': STEPS[step-1][2]
        }

        clazz, url, _ = STEPS[step-1]
        return clazz(self).process()

    def get_next_url(self):
        step = self.get_completed_step() or 0
        next_step = step + 1
        if next_step <= len(STEPS):
            _, url, _ = STEPS[next_step-1]
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

    def process_order(self, payment_form):
        """
        Takes the following steps:
        1.  Locks the products in the cart, read-only access only (TBD, I have no idea how to do this ATM)
        2.  Creates an Order instance from the form data in this checkout process, and validates it (it should checkout
            ok, if it doesn't there was a bug in my forms.
        3.  Authorize credit-card, payment information  (the payment form will have a hidden containing the amount to
            put on the card.  This way the number the user sees and the number I charge are guaranteed to be the same.
        4.  Submit the order (save it)
        5.  Decrement product stock
        6.  Unlock the products that were locked in step 1
        7.  Redirect the user to a receipt page
        """
        order, shipping_address, billing_address, order_items = self._build_order()
        if not payment_form.is_valid():
            return False

        order.transaction_id = 00000  # TODO: FIX THIS
        order.payment_status = Order.FUNDS_AUTHORIZED
        order.save()
        shipping_address.order = order
        shipping_address.save()
        billing_address.order = order
        billing_address.save()

        for item in order_items:
            item.order = order
            item.save()
            in_stock = item.product.quantity
            item.product.quantity = max(0, in_stock - item.quantity)
            item.product.save()

        for item in cartutils.get_cart_items(self.request):
            # empty the customer's cart
            item.delete()

        return True

    def _build_order(self):
        order = Order()
        shipping_address = None
        billing_address = None

        # populate the contact information
        contact_form = ContactInfoStep(self).get_saved_form()
        if contact_form.is_valid():
            cd = contact_form.cleaned_data
            order.first_name = cd['first_name']
            order.last_name = cd['last_name']
            order.email = cd['email']
            order.contact_method = cd['contact_method']
            order.phone = cd['phone']

        # populate the shipping information
        order.shipping_charge = decimal.Decimal('0.00')
        shipping_form = ShippingInfoStep(self).get_saved_form()
        if shipping_form.is_valid():
            shipping_address = shipping_form.save(OrderShippingAddress, commit=False)

        # populate the billing information
        billing_form = BillingInfoStep(self).get_saved_form()
        if billing_form.is_valid():
            billing_address = billing_form.save(OrderBillingAddress, commit=False)

        order.merchandise_total = round_cents(cartutils.cart_subtotal(self.request))
        order.sales_tax = round_cents((order.merchandise_total + order.shipping_charge) * decimal.Decimal('0.05'))
        return order, shipping_address, billing_address, self.get_order_items()

    def get_order_items(self):
        order_items = []
        for item in cartutils.get_cart_items(self.request):
            order_item = OrderItem()
            order_item.product = item.product
            order_item.quantity = item.quantity
            order_item.price = item.price
            # don't save them yet
            order_items.append(order_item)
        return order_items

    def get_user(self):
        """
        Returns the logged-in user associated with this request.  Will return None if the user is not authenticated, or
        if they are lazy
        """
        if self.request.user.is_authenticated() and not is_lazy_user(self.request.user):
            return self.request.user
        return None

    def get_customer_profile(self):
        """
        Returns the customer profile associated with this user, if one exists.  Otherwise returns None.
        """
        user = self.get_user()
        if user:
            profiles = CustomerProfile.objects.filter(user=self.request.user)
            if profiles.count() > 0:
                return profiles[0]
        return None


# defines the step ordering and the associated step url or the entire checkout process
STEPS = [(ContactInfoStep, reverse_lazy('contact'), 'Contact Info'),
         (ShippingInfoStep, reverse_lazy('shipping'), 'Shipping Info'),
         (BillingInfoStep, reverse_lazy('billing'), 'Billing Info'),
         (ReviewStep, reverse_lazy('review'), 'Review & Pay')]


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


def cancel(request):
    """
    Cancel this checkout.
    """
    co = Checkout(request)
    co.cancel()
    return HttpResponseRedirect(reverse('show_cart'))