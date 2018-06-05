from django.contrib import admin
from urllib.parse import urlparse
from django.utils.datastructures import MultiValueDictKeyError
from django.conf import settings
from expense.filters import ExpenseDateListFilter
from expense.models import Type , Category , HiddenCategory , Expense  

# Register your models here.
def get_user_id(request):
    """
    Gets the user id from the `user__id__exact` querystring paramter if it
    does not contains it will return with `None`.
    """
    try:
        return int(request.GET['user__id__exact'])
    except (MultiValueDictKeyError, ValueError):
        return None
def get_year(request):
    """
    Returns the querystring 'date__year' parameter or the current
    year. If it was not found then returns with `None`.
    """
    try:
        return int(request.GET['date__year'])
    except (MultiValueDictKeyError, ValueError):
        return None
def get_month(request):
    """
    Returns the querystring 'date__month' parameter or the current month.
    If it was not found then returns with `None`.
    """
    try:
        return int(request.GET['date__month'])
    except (MultiValueDictKeyError, ValueError):
        return None

class TypeAdmin(admin.ModelAdmin):
    """
    Admin interface for Expense groups.
    """
    list_display = ('name', )
    search_fields = ('name', )
    ordering = ('name', )

admin.site.register(Type, TypeAdmin)
class CategoryAdmin(admin.ModelAdmin):
    """
    Admin interface for expense categories.
    """
    list_display = ('type_name', 'name', )
    list_display_links = ('name', )
    search_fields = ('type', 'name', )
    ordering = ('type__name', 'name', )

admin.site.register(Category, CategoryAdmin)


class HiddenCategoryAdmin(admin.ModelAdmin):
    """
    Admin interface for hidden categories.
    """
    list_display = ('user_username', 'category_type_name',
                    'category_name', )
    list_display_links = ('user_username', )
    ordering = ('user__username', 'category__type__name', 'category__name', )


admin.site.register(HiddenCategory, HiddenCategoryAdmin)


class ExpenseAdmin(admin.ModelAdmin):
    """
    Admin interface for expenses.
    """
    class Media:
        css = {
            "all": (
                "expense/css/expense.css",
                )
        }

    list_display = ('date_str',
                    'category',
                    'description',
                    'formatted_amount')

    list_filter = ('user', ('date', ExpenseDateListFilter), 'category', )
    ordering = ('-date', )

    def get_form(self, request, obj=None, **kwargs):
        """
        Returns a Form class for use in the admin add view. This is used by
        add_view and change_view.
        """
        form = admin.ModelAdmin.get_form(self, request, obj=None, **kwargs)

        # setting the current user as initial value
        user_field = form.base_fields['user']
        user_field.initial = request.user.id
        return form

    def changelist_view(self, request, extra_context=None):
        """
        Extends the changelist_view with the following parameters:
        - statistics
        - selected year, month
        - title
        """
        user_id = get_user_id(request)
        year = get_year(request)
        month = get_month(request)
        # setting default parmeters if we did not came from the changelist
        # view.
        referer = urlparse(request.META.get('HTTP_REFERER', ''))
        if(referer.path != request.META.get('PATH_INFO', '')):
            user_id = request.user.id
            year = datetime.now().year
            month = datetime.now().month
            q = request.GET.copy()
            q['user__id__exact'] = str(user_id)
            q['date__year'] = str(year)
            q['date__month'] = str(month)
            request.GET = q
            request.META['QUERY_STRING'] = request.GET.urlencode()

        types_stat = Type.objects.get_statistics(user_id, year, month)
        title = 'Overall expenses'
        if year:
            title = ('Expenses of %s' % year)
        if month:
            d = datetime(year, month, 1)
            month_name = d.strftime("%B")
            title = ('Expenses of %s %s' % (month_name, year))

        extra_context = {
            'types_stat': types_stat,
            'current_year': year,
            'current_month': month,
            'current_user_id': user_id,
            'title': title,
            'media_dir': settings.MEDIA_URL + "/expense/"
        }

        return admin.ModelAdmin.changelist_view(self, request, extra_context)

admin.site.register(Expense, ExpenseAdmin)