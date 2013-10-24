from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from django.template import RequestContext
from forms import CheckBalanceForm
from django.views.decorators.debug import sensitive_post_parameters
from cart.forms import AddGiftCardToCartForm
from django.http import HttpResponseRedirect


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