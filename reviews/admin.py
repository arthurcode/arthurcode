from django.contrib import admin
from reviews.models import Review, ReviewFlag


class HasReviewFlagFilter(admin.SimpleListFilter):
    # the following three fields should be specified by the subclass
    flag = None
    title = "placeholder"
    parameter_name = "placeholder"

    def lookups(self, request, model_admin):
        return (
            ('True', 'Yes'),
            ('False', 'No'),
        )

    def queryset(self, request, queryset):
        if not self.value():
            return queryset

        flagged_comments = ReviewFlag.objects \
            .filter(flag=self.flag) \
            .values('review__pk') \
            .distinct('review__pk')

        if self.value() == "True":
            return queryset.filter(pk__in=flagged_comments)
        else:
            return queryset.exclude(pk__in=flagged_comments)


class IsFlaggedForRemovalFilter(HasReviewFlagFilter):
    title = 'is flagged for removal'
    parameter_name = 'flagged'
    flag = ReviewFlag.SUGGEST_REMOVAL


class IsApprovedFilter(HasReviewFlagFilter):
    title = 'is approved'
    parameter_name ='approved'
    flag = ReviewFlag.MODERATOR_APPROVAL


class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'rating', 'date_added', 'is_flagged_for_removal', 'is_approved')
    list_filter = ('product', 'rating', IsFlaggedForRemovalFilter, IsApprovedFilter)
    readonly_fields = ('date_added', 'last_modified')

admin.site.register(Review, ReviewAdmin)
