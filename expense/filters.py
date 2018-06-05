from django.contrib.admin.filters import DateFieldListFilter
from django.utils.translation import ugettext as _


class ExpenseDateListFilter(DateFieldListFilter):
    """
    A custom filter for the date field.

    It list all the available months, years of the Expenses objects.
    """
    def __init__(self, field, request, params, model, model_admin,
                 field_path=None):

        super(ExpenseDateListFilter, self).__init__(
            field, request, params, model, model_admin, field_path)

        self.links = [(_('Any date'), {}), ]

        months = model.objects.get_months()
        for m in months:
            self.links.append(
                (m.strftime("%B %Y"),
                 {'%s__year' % self.field.name: str(m.year),
                  '%s__month' % self.field.name: str(m.month)}))

        years = model.objects.get_years()
        for y in years:
            self.links.append(
                (y.strftime("%Y " + _("total")),
                 {'%s__year' % self.field.name: str(y.year)}))
