from lazysignup.decorators import allow_lazy_user
from lazysignup.utils import is_lazy_user
from django.core.urlresolvers import reverse_lazy, reverse
from django.http import HttpResponseRedirect
from accounts.forms import ContactInfoForm, CustomerShippingAddressForm, CustomerBillingAddressForm
from checkout.forms import PaymentInfoForm, ChooseShippingAddressByNickname
from django.shortcuts import render_to_response
from django.template import RequestContext
from cart import cartutils
from orders.models import Order, OrderShippingAddress, OrderBillingAddress, OrderItem, OrderTax
import decimal
from utils.util import round_cents
from accounts.models import CustomerProfile, CustomerShippingAddress, CustomerBillingAddress
from utils.validators import is_blank
import checkoututils
from decimal import Decimal
from django.views.decorators.http import require_GET
from accounts.accountutils import is_guest_passthrough


class PyOrder(object):
    """
    Represents an Order that is in the process of being created through the checkout process.
    This closely mirrors the Order DB model but because of all the foreign keys associated with the
    model it is difficult to work with before it has been saved.  This class is meant to make it easier to build an
    Order step-by-step.
    """

    def __init__(self, request):
        self.request = request
        self.items = None              # Order items
        self.shipping_address = None   # CustomerShippingAddress
        self.billing_address = None    # CustomerBillingAddress
        self.customer = None           # CustomerProfile
        self.first_name = None
        self.last_name = None
        self.email = None
        self.phone = None
        self.contact_method = None
        self.shipping_charge = None

    def tax_breakdown(self):
        """
        Returns a list of tupples in the following format:
        [ (tax name, tax rate, total), ...] eg. [(GST, 5, 10.00), (PST, 5, 10.00)]
        The totals are rounded to two decimal places.
        """
        if not self.shipping_address:
            return None

        taxes = checkoututils.sales_taxes(self.shipping_address.region)
        subtotal = self._taxable_total()
        breakdown = []

        for tax in taxes:
            breakdown.append((tax.description, tax.rate, round_cents((tax.rate/100) * subtotal)))
        return breakdown

    def merchandise_total(self):
        total = Decimal('0.00')
        for item in self.items:
            total += item.total
        return total

    def _taxable_total(self):
        return self.merchandise_total() + self.shipping_charge

    def total(self):
        total = self._taxable_total()
        tax_breakdown = self.tax_breakdown()
        for tax in tax_breakdown:
            total += tax[2]
        return total

class Step(object):

    data_key = 'step'
    extra_context = {}

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

    def visit(self, order):
        """
        Transfer the data collected in this step to the order object.
        Subclasses should override.
        """
        return

    def is_complete(self):
        """
        Return 'True' if this step has already been marked as completed, and 'False' otherwise.
        """
        highest_completed_step = self.checkout.get_completed_step()
        this_step_num = self.checkout.get_step_number(self)
        return this_step_num <= highest_completed_step


class ContactInfoStep(Step):

    data_key = 'contact'
    form_key = 'contact_form'

    def _get(self):
        form = self.get_saved_form()
        if not form.is_bound:
            # there was no saved data, this is the first time the user is seeing this form in this checkout.
            data = self.get_existing_contact_info()
            if not self.is_complete():
                test_form = ContactInfoForm(self.request, data=data)
                if test_form.is_valid():
                    # we have all the information we need saved in the user's profile.  Don't bore them with it again.
                    # They can modify the info later if required.
                    self.save(self.form_key, data)
                    self.mark_complete()
                    return HttpResponseRedirect(self.checkout.get_next_url())
            form = ContactInfoForm(self.checkout.request, initial=data)
        return self._render_form(form)

    def _render_form(self, form, template='contact_info.html'):
        context = {
            'form': form,
            'user': self.checkout.get_user(),
            'profile': self.checkout.get_customer_profile(),
        }
        if self.checkout.extra_context:
            context.update(self.checkout.extra_context)
        return render_to_response(template, context, context_instance=RequestContext(self.request))

    def _post(self):
        data = self.request.POST.copy()
        form = ContactInfoForm(self.checkout.request, data=data)
        if form.is_valid():
            self.save(self.form_key, data)
            self.checkout._mark_step_complete(self)
            return HttpResponseRedirect(self.checkout.get_next_url())
        return self._render_form(form)

    def get_saved_form(self):
        saved_data = self.get(self.form_key, None)
        return ContactInfoForm(self.checkout.request, data=saved_data)

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
                self._add_to_data('phone', profile.phone, data)
                self._add_to_data('contact_method', profile.contact_method, data)
                self._add_to_data('on_mailing_list', profile.on_mailing_list, data)
        return data

    def _add_to_data(self, key, value, data):
        if not is_blank(value):
            data[key] = value

    def save_data_to_profile(self):
        form = self.get_saved_form()
        if not form.is_valid():
            return
        user = self.checkout.get_user()
        if not user:
            return
        cd = form.cleaned_data
        user.email = cd['email']
        user.first_name = cd['first_name']
        user.last_name = cd['last_name']
        user.full_clean()
        user.save()

        profile = self.checkout.get_customer_profile()
        if not profile:
            profile = CustomerProfile(user=user)
        profile.contact_method = cd['contact_method']
        profile.on_mailing_list = cd['on_mailing_list']
        if 'phone' in cd:
            profile.phone = cd['phone']
        profile.full_clean()
        profile.save()

    def visit(self, order):
        """
        Transfer contact information to the order object.
        """
        form = self.get_saved_form()
        if form.is_valid():
            cd = form.cleaned_data
            order.first_name = cd['first_name']
            order.last_name = cd['last_name']
            order.email = cd['email']
            order.contact_method = cd['contact_method']
            order.phone = cd['phone']
        profile = self.checkout.get_customer_profile()
        if not profile:
            # create a profile for this user if one doesn't yet exist (even if they are a guest user)
            profile = CustomerProfile(user=self.request.user)
        order.customer = profile


class ShippingInfoStep(Step):
    data_key = "shipping"
    form_key = "shipping_form"

    def _get(self):
        if not self.is_complete():
            # check if a nickname has been selected.  If one has, and we have all the data we need, mark the step complete.
            nickname = self.get_nickname(None)
            if nickname:
                form = self.get_form_for_nickname(nickname, None)
                if form.is_valid():
                    self.save(self.form_key, form.data)
                    self.mark_complete()
                    return HttpResponseRedirect(self.checkout.get_next_url())

            # if we only have one saved shipping address, just use it and ask the customer to confirm their data in the
            # last step
            existing_nicknames = self.get_existing_nicknames()
            if len(existing_nicknames) == 1:
                nickname = existing_nicknames[0]
                form = self.get_form_for_nickname(nickname, None)
                if form.is_valid():
                    self.save(self.form_key, form.data)
                    self.mark_complete()
                    return HttpResponseRedirect(self.checkout.get_next_url())
        saved_data = self.get(self.form_key, {})
        nickname = self.get_nickname(saved_data)
        form = self.get_form_for_nickname(nickname, saved_data)
        return self._render_form(form, nickname)

    def get_nickname(self, saved_data):
        nickname = self.request.GET.get(ChooseShippingAddressByNickname.SHIP_TO_KEY, None)
        if not nickname and saved_data:
            nickname = saved_data.get('nickname', None)
        return nickname

    def get_form_for_nickname(self, nickname, saved_data=None):
        if not nickname:
            # can't display any kind of a form until a nickname is chosen
            return None

        use_saved_data = False

        if saved_data:
            saved_nickname = saved_data.get('nickname', None)
            if nickname == ChooseShippingAddressByNickname.NEW_ADDRESS_NICKNAME and saved_nickname not in self.get_existing_nicknames() \
                and saved_nickname != ChooseShippingAddressByNickname.ME_NICKNAME:
                use_saved_data = True
            elif saved_nickname == nickname:
                use_saved_data = True

        data = None
        if use_saved_data:
            data = saved_data

        profile = self.checkout.get_customer_profile()
        address = None
        address_id = None

        if profile:
            addresses = profile.shipping_addresses.filter(nickname=nickname)
            if addresses.count() > 0:
                address = addresses[0]
                address_id = address.id

        if address and not use_saved_data:
            data = address.as_dict()

        initial = None
        if nickname == ChooseShippingAddressByNickname.ME_NICKNAME:
            order = self.checkout.extra_context['order']
            if not order:
                order = self.checkout.build_order()

            initial = {
                'name': "%s %s" % (order.first_name, order.last_name),
                'nickname': ChooseShippingAddressByNickname.ME_NICKNAME,
                'phone': order.phone,
            }

        return CustomerShippingAddressForm(profile, address_id=address_id, data=data, initial=initial)

    def _post(self):
        """
        Validate the address form and if applicable move to the next step.
        """
        post_data = self.request.POST.copy()
        form = CustomerShippingAddressForm(self.request.user.get_customer_profile(), data=post_data)

        if form.is_valid():
            self.save(self.form_key, post_data)
            self.mark_complete()
            return HttpResponseRedirect(self.checkout.get_next_url())
        return self._render_form(form, self.request.GET.get(ChooseShippingAddressByNickname.SHIP_TO_KEY, None) or post_data.get('nickname'))

    def _render_form(self, form, nickname):
        selected_nickname = nickname

        if nickname and nickname != ChooseShippingAddressByNickname.ME_NICKNAME and nickname not in self.get_existing_nicknames():
            selected_nickname = ChooseShippingAddressByNickname.NEW_ADDRESS_NICKNAME
        select_form = ChooseShippingAddressByNickname(self.request, initial={ChooseShippingAddressByNickname.SHIP_TO_KEY: selected_nickname})

        context = {
            'form': form,
            'select_form': select_form,
            'selected_nickname': selected_nickname,
        }
        if self.extra_context:
            context.update(self.extra_context)
        if self.checkout.extra_context:
            context.update(self.checkout.extra_context)
        return render_to_response('shipping_form.html', context, context_instance=RequestContext(self.request))

    def visit(self, order):
        order.shipping_address = self.get_address()
        order.shipping_charge = decimal.Decimal('5')

    def get_existing_nicknames(self):
        """
        Returns the nicknames that identify this customer's saved shipping addresses.  Returns and empty list if the
        customer doesn't have a profile or if there aren't any addresses associated with the profile.
        """
        profile = self.checkout.get_customer_profile()
        if not profile:
            return []
        return [a.nickname for a in profile.shipping_addresses.all()]

    def save_address_to_profile(self):
        profile = self.checkout.get_customer_profile()
        if not profile:
            profile = CustomerProfile(user=self.request.user)
            profile.full_clean()
            profile.save()
        address = self.get_address()
        address.full_clean()
        address.save()

    def get_address(self):
        form = CustomerShippingAddressForm(self.request.user.get_customer_profile(), data=self.get(self.form_key))
        if form.is_valid():
            return form.save(CustomerShippingAddress, commit=False)
        # This shouldn't happen, but I guess you never do know
        return None


class BillingInfoStep(Step):

    data_key = 'billing'
    form_key = 'billing_form'
    form_clazz = CustomerBillingAddressForm
    addr_clazz = CustomerBillingAddress
    template = 'billing_form.html'

    def __init__(self, *args, **kwargs):
        super(BillingInfoStep, self).__init__(*args, **kwargs)
        self.extra_context = {
            'shipping_address': ShippingInfoStep(self.checkout).get_address()
        }

    def _get(self):
        form = self.get_saved_form()
        if not self.is_complete() and form.is_valid():
            # we already have the information we need!
            self.save(self.form_key, form.data)
            self.mark_complete()
            return HttpResponseRedirect(self.checkout.get_next_url())
        return self._render_form(form)

    def _post(self):
        post_data = self.request.POST.copy()
        form = self.form_clazz(self.request.user.get_customer_profile(), data=post_data)
        if form.is_valid():
            self.save(self.form_key, post_data)
            self.mark_complete()
            return HttpResponseRedirect(self.checkout.get_next_url())
        return self._render_form(form)

    def _render_form(self, form):
        context = {
            'form': form
        }
        if self.extra_context:
            context.update(self.extra_context)
        if self.checkout.extra_context:
            context.update(self.checkout.extra_context)
        return render_to_response(self.template, context, context_instance=RequestContext(self.request))

    def get_customer_address(self):
        """
        Returns the billing address associated with this user's profile.
        """
        profile = self.checkout.get_customer_profile()
        if not profile:
            return None
        try:
            return profile.billing_address
        except CustomerBillingAddress.DoesNotExist:
            # the reverse of a one-to-one relationship will throw DoesNotExist if there is no billing address
            # associated with the profile.  Something to watch out for.
            return None

    def get_saved_form(self):
        """
        Returns the saved billing form data, or data that already exists in the form of a saved billing address.
        """
        form_data = self.get(self.form_key, None)
        address = self.get_customer_address()
        if not form_data:
            if address:
                form_data = address.as_dict()
        # are we editing an existing address or creating a new one?
        address_id = None
        if address:
            address_id = address.id
        return self.form_clazz(self.request.user.get_customer_profile(), address_id=address_id, data=form_data)

    def get_address(self):
        form = self.get_saved_form()
        if form.is_valid():
            return form.save(self.addr_clazz, commit=False)

    def visit(self, order):
        order.billing_address = self.get_address()

    def save_address_to_profile(self):
        profile = self.checkout.get_customer_profile()
        if not profile:
            profile = CustomerProfile(user=self.request.user)
            profile.full_clean()
            profile.save()
        address = self.get_address()
        address.full_clean()
        address.save()


class ReviewStep(Step):

    data_key = 'review'

    def _get(self):
        form = PaymentInfoForm()
        return self._render_form(form)

    def _render_form(self, form):
        order = self.checkout.build_order()
        if not form.is_bound:
            form.fields['total'].initial = order.total

        context = {
            'form': form,
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

    def finish(self):
        """
        Should be called after the checkout successfully completes.
        """
        for item in cartutils.get_cart_items(self.request):
            # empty the customer's cart
            item.delete()

        # save the shipping and billing addresses, if necessary
        ContactInfoStep(self).save_data_to_profile()
        ShippingInfoStep(self).save_address_to_profile()
        BillingInfoStep(self).save_address_to_profile()

    def is_finished(self):
        return self.get_completed_step() == len(STEPS)

    def is_in_progress(self):
        return self.is_started() and not self.is_finished()

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

    def get_step_url(self, step):
        num = self.get_step_number(step)
        return STEPS[num-1][1]

    def _mark_step_complete(self, step):
        # only store the highest completed step
        step_num = self.get_step_number(step)

        if step_num > self.get_completed_step():
            self.save('step', step_num)
        if self.is_finished():
            # call the cleanup routine
            self.finish()

    def _mark_step_incomplete(self, step):
        highest_completed_step = self.get_completed_step()

        if not highest_completed_step:
            # the user hasn't completed any steps
            return
        step_num = self.get_step_number(step)

        if step_num > highest_completed_step:
            # nothing to do.  This really shouldn't happen but I guess it doesn't hurt to handle it.
            return

        new_highest_completed_step = step_num - 1

        if new_highest_completed_step > 0:
            # technically the user could have finished steps beyond this one, but we want to prevent them from moving
            # forward until step_num is complete.  When they get to the steps that were previously completed we should
            # pull out any saved data from the session to make it easier for them to move past the steps they finished
            # previously.
            self.save('step', new_highest_completed_step)
        else:
            # we effectively have to start over
            self.save('step', None)

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
            'current_step_name': STEPS[step-1][2],
            'order': self.build_order(),
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
        order_id = self.get('order', None)
        if order_id:
            return reverse('order_detail', kwargs={'order_id': order_id})
        # for some reason there is no saved order id, redirect to the cart page
        return reverse('show_cart')

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
        pyOrder = self.build_order()  # python class
        order = Order()               # db class

        if not payment_form.is_valid():
            return False

        # link customer information
        order.customer = pyOrder.customer
        order.first_name = pyOrder.first_name
        order.last_name = pyOrder.last_name
        order.email = pyOrder.email
        order.phone = pyOrder.phone
        order.contact_method = pyOrder.contact_method

        # contact paypal to authorize the transfer of funds
        order.shipping_charge = pyOrder.shipping_charge
        order.transaction_id = 00000  # TODO: FIX THIS
        order.payment_status = Order.FUNDS_AUTHORIZED
        order.save()

        shipping_address = pyOrder.shipping_address.as_address(OrderShippingAddress)
        shipping_address.order = order
        shipping_address.save()

        billing_address = pyOrder.billing_address.as_address(OrderBillingAddress)
        billing_address.order = order
        billing_address.save()

        for order_item in pyOrder.items:
            order_item.order = order
            order_item.save()
            in_stock = order_item.item.quantity
            order_item.item.quantity = max(0, in_stock - order_item.quantity)
            order_item.item.save()

        for (name, rate, total) in pyOrder.tax_breakdown():
            orderTax = OrderTax(name=name, rate=rate, total=total, order=order)
            orderTax.save()

        # save the order-id in the session dictionary
        self.save('order', order.id)
        return True

    def build_order(self):
        """
        Builds a PyOrder object using the data that has been collected from this checkout process.
        Only the steps that have been completed will be used to collect the data.  This order is NOT saved to the
        database at this point.
        """
        order = PyOrder(self.request)
        order.items = self.get_order_items()

        completed_step = self.get_completed_step()
        if completed_step is None:
            return order

        for i in range(completed_step):
            STEPS[i][0](self).visit(order)
        return order

    def get_order_items(self):
        order_items = []
        for cart_item in cartutils.get_cart_items(self.request):
            order_item = OrderItem()
            order_item.item = cart_item.item
            order_item.quantity = cart_item.quantity
            order_item.price = cart_item.price
            # don't save them yet
            order_items.append(order_item)
        return order_items

    def get_user(self):
        """
        Returns the logged-in user associated with this request.  May return a lazy user.
        """
        if self.request.user.is_authenticated():
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
STEPS = [(ContactInfoStep, reverse_lazy('checkout_contact'), 'Contact Info'),
         (ShippingInfoStep, reverse_lazy('checkout_shipping'), 'Shipping Info'),
         (BillingInfoStep, reverse_lazy('checkout_billing'), 'Billing Info'),
         (ReviewStep, reverse_lazy('checkout_review'), 'Review & Pay')]


@require_GET
@allow_lazy_user
def checkout(request):
    """
    Checkout a logged-in user.
    """
    co = Checkout(request)
    if is_lazy_user(request.user) and not co.is_in_progress():
        if not is_guest_passthrough(request):
            # redirect to the login view where they can explicitly choose to login or checkout as a guest
            login_url = reverse('login_or_create_account')
            checkout_url = reverse('checkout')
            redirect_url = "%s?next=%s" % (login_url, checkout_url)
            return HttpResponseRedirect(redirect_url)
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