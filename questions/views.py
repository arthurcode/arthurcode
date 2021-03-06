from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.http import HttpResponseForbidden
from catalogue.models import Product
from comments.models import MPTTComment
from questions.forms import AskQuestionForm, EditQuestionForm, AnswerQuestionForm
from django.views.decorators.http import require_GET
from comments.views.comment import CommentPostBadRequest
from accounts.decorators import public_profile_required_for_regular_users, anonymous_users_choose_guest
from django.contrib.admin.views.decorators import staff_member_required
from urllib import urlencode

@anonymous_users_choose_guest
@public_profile_required_for_regular_users
def ask_view(request, product_slug):
    product = get_object_or_404(Product, slug=product_slug)

    if request.method == "POST":
        post_data = request.POST.copy()
        form = AskQuestionForm(request, product, data=post_data)
        if form.is_valid():
            question = form.get_comment_object()
            question.save()
            return HttpResponseRedirect(show_question_url(question.id, created=True))
        elif form.security_errors():
            return CommentPostBadRequest(u"Security errors in form.")
    else:
        form = AskQuestionForm(request, product)

    context = {
        'product': product,
        'form': form,
    }
    return render_to_response('ask_question.html', context, context_instance=RequestContext(request))


@require_GET
def show_view(request, id):
    if request.GET.get('deleted', False):
        question = None
        product = get_object_or_404(Product, id=request.GET.get('product_id', None))
    else:
        question = get_object_or_404(MPTTComment, id=id)
        product = question.content_object

    context = {
        'question': question,
        'product': product,
    }
    context.update(request.GET.copy())
    return render_to_response('show_question.html', context, context_instance=RequestContext(request))


def edit_view(request, id):
    question = get_object_or_404(MPTTComment, id=id)
    if not question.user == request.user:
        return HttpResponseForbidden(u"You do not have permission to edit this question.")

    if request.method == "POST":
        post_data = request.POST.copy()
        form = EditQuestionForm(request, question, data=post_data)
        if form.is_valid():
            form.save_changes()
            return HttpResponseRedirect(show_question_url(id, edited=True))
    else:
        form = EditQuestionForm(request, question)

    context = {
        'question': question,
        'form': form,
        'product': question.content_object,
    }
    return render_to_response('edit_question.html', context, context_instance=RequestContext(request))


def delete_view(request, id):
    question = get_object_or_404(MPTTComment, id=id)
    if not question.user.is_staff and not question.user == request.user:
        return HttpResponseForbidden(u"You do not have permission to delete this question.")

    if request.method == "POST":
        if "yes" in request.POST:
            question.delete()
            return HttpResponseRedirect(show_question_url(id, deleted=True, product_id=question.object_pk))
        else:
            return HttpResponseRedirect(show_question_url(id))

    context = {
        'question': question,
        'product': question.content_object,
    }
    return render_to_response('delete_question.html', context, context_instance=RequestContext(request))


@staff_member_required
def answer_view(request, id):
    question = get_object_or_404(MPTTComment, id=id)

    if request.method == "POST":
        post_data = request.POST.copy()
        form = AnswerQuestionForm(request, question, data=post_data)
        if form.is_valid():
            answer = form.get_comment_object()
            answer.full_clean()
            answer.save()
            return HttpResponseRedirect(question.get_absolute_url())
    else:
        form = AnswerQuestionForm(request, question)

    context = {
        'question': question,
        'form': form,
    }
    return render_to_response('answer_question.html', context, context_instance=RequestContext(request))


def show_question_url(qid, created=False, deleted=False, edited=False, product_id=None):
    path = reverse('show_question', kwargs={'id': qid})
    params = {}

    if created:
        params['created'] = True
    if deleted:
        params['deleted'] = True
        params['product_id'] = product_id
    if edited:
        params['edited'] = True

    if params:
        path += "?" + urlencode(params)
    return path


