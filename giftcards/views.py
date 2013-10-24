from django.shortcuts import render_to_response
from django.template import RequestContext
from forms import CheckBalanceForm
from django.views.decorators.debug import sensitive_post_parameters


def home_view(request):
    return render_to_response('gc_home.html', {}, context_instance=RequestContext(request))


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