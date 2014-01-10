from forms import SubscribeToMailingListForm
from django.shortcuts import render_to_response, HttpResponseRedirect
from django.template import RequestContext
from django.views.decorators.http import require_GET
from django.core.urlresolvers import reverse

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

