from forms import SubscribeToMailingListForm
from django.shortcuts import render_to_response, HttpResponseRedirect
from django.template import RequestContext
from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.core.signing import Signer
import utils

def subscribe(request):
    if request.method == "POST":
        data = request.POST.copy()
        form = SubscribeToMailingListForm(request, data=data)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('subscribe_complete'))
    else:
        form = SubscribeToMailingListForm(request)

    context = {
        'form': form,
    }
    return render_to_response('subscribe.html', context, context_instance=RequestContext(request))


@require_GET
def subscribe_complete(request):
    return render_to_response('subscribe_complete.html', {}, context_instance=RequestContext(request))

@login_required
@require_GET
def unsubscribe_user(request):
    """
    An unsubscribe view that is available to logged in users.
    """
    signer = Signer()
    signed_email = signer.sign(request.user.email)
    return HttpResponseRedirect(reverse('unsubscribe', args=[signed_email]))


def unsubscribe(request, email_token):
    email = Signer().unsign(email_token)

    if request.method == "POST":
        data = request.POST.copy()
        if 'cancel' in data:
            # TODO: maybe pass a next link along to this view?
            return HttpResponseRedirect(reverse('home'))
        else:
            utils.remove_from_list(email)
            return HttpResponseRedirect(reverse('unsubscribe_complete'))

    context = {
        'email': email,
    }
    return render_to_response('unsubscribe.html', context, context_instance=RequestContext(request))


def unsubscribe_complete(request):
    return render_to_response('unsubscribe_complete.html', {}, context_instance=RequestContext(request))

