from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.contrib.admin.views.decorators import staff_member_required
from catalogue.models import Product
from reviews.forms import AddReviewForm, EditReviewForm, FlagReviewForm, AdminDeleteReviewForm
from reviews.models import Review, ReviewFlag
from utils.storeutils import get_products_needing_review
from reviews.signals import review_deleted
from accounts.decorators import public_profile_required

@login_required
@public_profile_required()
def create_review(request, product_slug):
    product = get_object_or_404(Product, slug=product_slug)
    try:
        Review.objects.get(product=product, user=request.user)
        # A review already exists, forward them to the edit url
        return HttpResponseRedirect(edit_review_url(product))
    except Review.DoesNotExist:
        pass

    if request.method == "POST":
        post_data = request.POST.copy()
        form = AddReviewForm(request, product, data=post_data)
        if form.is_valid():
            form.create_review()
            return HttpResponseRedirect(get_view_url(product, created=True))
    else:
        form = AddReviewForm(request, product)

    context = {
        'product': product,
        'form': form,
    }
    return render_to_response("product_review.html", context, context_instance=RequestContext(request))


@login_required
@public_profile_required()
def edit_review(request, product_slug):
    product = get_object_or_404(Product, slug=product_slug)
    try:
        review = Review.objects.select_related('user__public_profile', 'product').get(product=product, user=request.user)
    except Review.DoesNotExist:
        # there is no review to edit, forward them to the create-review url
        return HttpResponseRedirect(create_review_url(product))

    if request.method == "POST":
        post_data = request.POST.copy()
        form = EditReviewForm(request, review, data=post_data)
        if form.is_valid():
            form.edit_review()
            return HttpResponseRedirect(get_view_url(product, edited=True))
    else:
        form = EditReviewForm(request, review)

    context = {
        'form': form,
        'product': product,
        'review': review,
    }
    return render_to_response("edit_review.html", context, context_instance=RequestContext(request))


@login_required
def delete_review(request, product_slug):
    product = get_object_or_404(Product, slug=product_slug)
    try:
        review = Review.objects.get(product=product, user=request.user)
    except Review.DoesNotExist:
        return HttpResponseRedirect(create_review_url(product))

    if request.method == "POST":
        if "yes" in request.POST:
            review.delete()
            review_deleted.send(sender=review)
            return HttpResponseRedirect(get_view_url(product, deleted=True))
        else:
            return HttpResponseRedirect(get_view_url(product))

    context = {
        'product': product,
        'review': review,
    }
    return render_to_response('delete_review.html', context, context_instance=RequestContext(request))


@login_required
def view_review(request, product_slug):
    product = get_object_or_404(Product, slug=product_slug)
    try:
        review = Review.objects.get(product=product, user=request.user)
    except Review.DoesNotExist:
        was_deleted = request.GET.get('deleted', False)
        if not was_deleted:
            return HttpResponseRedirect(create_review_url(product))
        review = None

    context = {
        'product': product,
        'review': review,
        'needing_review': get_products_needing_review(request).exclude(id=product.id),
    }
    context.update(request.GET.copy())  # state cues
    return render_to_response('view_review.html', context, context_instance=RequestContext(request))


def create_review_url(product):
    return reverse('create_product_review', kwargs={'product_slug': product.slug})


def edit_review_url(product):
    return reverse('edit_product_review', kwargs={'product_slug': product.slug})


def get_view_url(product, edited=False, created=False, deleted=False):
    path = reverse('your_review', kwargs={'product_slug': product.slug})
    if edited or created or deleted:
        path += '?'
        if edited:
            path += 'edited=True'
        if created:
            path += 'created=True'
        if deleted:
            path += 'deleted=True'
    return path


def flag(request, id):
    """
    Flags the given review for removal.
    """
    review = get_object_or_404(Review, id=id)
    form = None

    if request.method == "POST":
        post_data = request.POST.copy()
        if 'yes' in post_data:
            form = FlagReviewForm(request, review, data=post_data)
            if form.is_valid():
                form.do_flag()
                return HttpResponseRedirect(review.get_absolute_url())
        else:
            return HttpResponseRedirect(review.get_absolute_url())

    form = form or FlagReviewForm(request, review)

    context = {
        'review': review,
        'form': form,
        'product': review.product,
    }
    return render_to_response("flag_review.html", context, context_instance=RequestContext(request))


@staff_member_required
def approve(request, id):
    review = get_object_or_404(Review, id=id)
    if not review.is_approved():
        if request.method == "POST":
            flag = ReviewFlag(user=request.user, flag=ReviewFlag.MODERATOR_APPROVAL, review=review)
            flag.full_clean()
            flag.save()
    return HttpResponseRedirect(review.get_absolute_url())


@staff_member_required
def withdraw_approval(request, id):
    review = get_object_or_404(Review, id=id)
    if review.is_approved():
        if request.method == "POST":
            flag = review.get_approval_flag()
            if flag:
                flag.delete()
    return HttpResponseRedirect(review.get_absolute_url())


@staff_member_required
def admin_delete(request, id):
    """
    A staff member can use this view to delete an inappropriate review.
    """
    review = get_object_or_404(Review, id=id)

    if request.method == "POST":
        post_data = request.POST.copy()
        form = AdminDeleteReviewForm(request, review, data=post_data)
        if form.is_valid():
            form.delete_review()
            return HttpResponseRedirect(review.product.get_absolute_url())
    else:
        form = AdminDeleteReviewForm(request, review)

    context = {
        'review': review,
        'form': form,
        'product': review.product,
    }
    return render_to_response("admin_delete_review.html", context, context_instance=RequestContext(request))

