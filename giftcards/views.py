from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from django.template import RequestContext
from forms import CheckBalanceForm
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_POST
from cart.forms import AddGiftCardToCartForm
from django.http import HttpResponseRedirect
from utils.decorators import ajax_required
from cart.cartutils import add_gift_card_to_cart, cart_subtotal, cart_distinct_item_count
from cart.forms import AddGiftCardToCartForm


def home_view(request):
    if request.method == "POST":
        data = request.POST.copy()
        form = AddGiftCardToCartForm(data=data)
        if form.is_valid():
            form.save(request)
            return HttpResponseRedirect(reverse('show_cart'))
    else:
        form = AddGiftCardToCartForm()

    context = {
        'form': form,
    }
    return render_to_response('gc_home.html', context, context_instance=RequestContext(request))


@sensitive_post_parameters()
def check_balance_view(request):
    balance = None

    if request.method == "POST":
        data = request.POST.copy()
        form = CheckBalanceForm(data=data)
        if form.is_valid():
            balance = form.check_balance()
    else:
        form = CheckBalanceForm()

    context = {
        'form': form,
        'balance': balance,
    }
    return render_to_response('gc_check_balance.html', context, context_instance=RequestContext(request))


@ajax_required
@require_POST
def add_gift_card_to_cart(request):
    data = request.POST.copy()
    form = AddGiftCardToCartForm(data=data)
    if form.is_valid():
        gc = form.save(request)
        context = {
            'item': gc,
            'subtotal': cart_subtotal(request),
            'items_in_cart': cart_distinct_item_count(request),
            'quantity': 1,
        }
        return render_to_response('post_add_gc_to_cart_summary.html', context, context_instance=RequestContext(request))
    else:
        raise Exception("form error")