from django.contrib import admin
from search.models import SearchTerm


class SearchTermAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'hits', 'ip_address', 'search_date')
    exclude = ('user',)


admin.site.register(SearchTerm, SearchTermAdmin)
