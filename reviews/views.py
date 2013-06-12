from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden

from catalogue.models import Product
from reviews.forms import AddReviewForm, EditReviewForm
from reviews.models import Review
from utils.storeutils import get_products_needing_review
from accounts.models import PublicProfile
from reviews.signals import review_deleted

@login_required
def review_view(request, product_slug):

    if request.method == 'GET':
        #TODO: turn this into a decorator
        try:
            request.user.public_profile
        except PublicProfile.DoesNotExist:
            return HttpResponseRedirect(reverse('create_public_profile') + "?next=" + request.path)

    product = get_object_or_404(Product, slug=product_slug)
    review = None
    try:
        review = Review.objects.select_related('user__public_profile', 'product').get(product=product, user=request.user)
    except Review.DoesNotExist:
        pass

    context = {
        'product': product,
        'review': review,
        'needing_review': get_products_needing_review(request).exclude(id=product.id)
    }

    if not review:
        return _add_review(request, product, context)
    return _edit_review(request, review, product, context)


def _add_review(request, product, context):
    if request.method == "POST":
        post_data = request.POST.copy()
        form = AddReviewForm(request, product, data=post_data)
        if form.is_valid():
            review = form.create_review()
            return HttpResponseRedirect(review.after_create_url())
    else:
        context.update(request.GET.copy())
        form = AddReviewForm(request, product)

    context['form'] = form
    return render_to_response("product_review.html", context, context_instance=RequestContext(request))


def _edit_review(request, review, product, context):
    if request.method == "POST":
        post_data = request.POST.copy()
        if "delete" in post_data:
            if not request.user == review.user:
                return HttpResponseForbidden(u'You do not have permission to delete this review.')
            review.delete()
            review_deleted.send(sender=review)
            return HttpResponseRedirect(review.after_delete_url())
        if "cancel" in post_data:
            return HttpResponseRedirect(reverse('product_review', kwargs={'slug': product.slug}))
        form = EditReviewForm(request, review, data=post_data)
        if form.is_valid():
            form.edit_review()
            return HttpResponseRedirect(review.after_edit_url())
    else:
        form = EditReviewForm(request, review)
        context.update(request.GET.copy())

    context['form'] = form
    return render_to_response("edit_review.html", context, context_instance=RequestContext(request))
