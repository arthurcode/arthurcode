from lazysignup.decorators import allow_lazy_user
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.http import HttpResponseForbidden
from catalogue.models import Product
from comments.models import MPTTComment
from questions.forms import AskQuestionForm, EditQuestionForm
from django.views.decorators.http import require_GET
from comments.views.comment import CommentPostBadRequest
from accounts.accountutils import is_regular_user, is_lazy_user


@allow_lazy_user
def ask_view(request, product_slug):
    product = get_object_or_404(Product, slug=product_slug)

    if request.method == "POST":
        post_data = request.POST.copy()
        form = AskQuestionForm(request, product, data=post_data)
        if form.is_valid():
            question = form.get_comment_object()
            question.save()
            return HttpResponseRedirect(reverse('show_question', kwargs={'id': question.id}))
        elif form.security_errors():
            return CommentPostBadRequest(u"Security errors in form.")
    else:
        if is_lazy_user(request.user) and not 'guest' in request.GET:
            redirect_to = reverse('login_or_create_account') + "?next=" + request.path
            return HttpResponseRedirect(redirect_to)
        if is_regular_user(request.user) and not request.user.get_public_profile():
            # require logged-in users to create a public profile
            redirect_to = reverse('create_public_profile') + "?next=" + request.path
            return HttpResponseRedirect(redirect_to)
        form = AskQuestionForm(request, product)

    context = {
        'product': product,
        'form': form,
    }
    return render_to_response('ask_question.html', context, context_instance=RequestContext(request))


@require_GET
def show_view(request, id):
    question = get_object_or_404(MPTTComment, id=id)
    context = {'question': question}
    return render_to_response('show_question.html', context, context_instance=RequestContext(request))