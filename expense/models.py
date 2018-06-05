from django.db import models

# Create your models here.

from django.db.models import Sum
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
#from expense.templatetags import numberformat
from django.db.models import Q


class TypeManager(models.Manager):
    """
    Manager class of Type objects.
    """
    def get_statistics(self, user_id, year, month):
        """
        Creates a statistic query by the given parameters.
        """
        types = Type.objects.all()
        cat_filter = Q()
        if user_id:
            cat_filter = Q(expenses__user__id=user_id)
        if year:
            cat_filter = cat_filter & Q(expenses__date__year=year)
        if month:
            cat_filter = cat_filter & Q(expenses__date__month=month)

        for t in types:
            t.category_list = t.categories.filter(cat_filter).annotate(
                category_total=Sum('expenses__amount'))

            total = t.category_list.aggregate(total=Sum('category_total'))
            t.total = total['total']
        return types


class ExpenseManager(models.Manager):
    """
    Manager class of Expense objects.
    """
    def get_months(self):
        """
        Return the list of the months where expense objects are
        recorded.
        """
        return Expense.objects.dates('date', 'month', order='DESC')

    def get_years(self):
        """
        Returns the list of the where expense objects are
        recorded.
        """
        return Expense.objects.dates('date', 'year', order='DESC')


class Type(models.Model):
    """
    Expense groups are represented by this model.
    """
    name = models.CharField(_('name'), max_length=50)

    objects = TypeManager()

    class Meta:
        verbose_name_plural = _('types')
        verbose_name = _('type')
        ordering = ['name']

    def __str__(self):
        return self.name


class Category(models.Model):
    """
    Expense categories are represented by this model.
    """
    name = models.CharField(_('name'), max_length=50)
    type = models.ForeignKey(Type, related_name='categories',
                             blank=False, null=True)

    class Meta:
        verbose_name_plural = _('categories')
        verbose_name = _('category')
        ordering = ['type__name', 'name']

    def __str__(self):
        return ("%s - %s" % (self.type.name,  self.name))

    def type_name(self):
        return self.type.name


class HiddenCategory(models.Model):
    """
    Not all users wish to see the same category list.
    If you have many categories it is easier to have a smaller list.
    """
    user = models.ForeignKey(User, blank=False, null=True)
    category = models.ForeignKey(Category,  blank=True, null=True)

    class Meta:
        verbose_name_plural = _('hidden categories')
        verbose_name = _('hidden category')
        ordering = ['user__username', 'category__type__name', 'category__name']
        unique_together = (('user', 'category'))

    def __str__(self):
        return ("%s - %s - %s") % (self.user.username, self.category.type.name,
                                   self.category.name)

    def category_type_name(self):
        return self.category.type.name

    def user_username(self):
        return self.user.username

    def category_name(self):
        return self.category.name


class Expense(models.Model):
    """
    Expenses are represented by this model.
    """
    user = models.ForeignKey(User, blank=False, null=True)
    category = models.ForeignKey(Category, related_name='expenses', blank=True,
                                 null=True)
    date = models.DateField(_('date'), 'date')
    description = models.CharField(_('description'), max_length=300)
    amount = models.IntegerField(_('amount'))
    objects = ExpenseManager()
    date.expense_date_filter = True

    class Meta:
        verbose_name_plural = _('expenses')
        verbose_name = _('expense')
        ordering = ['-date', 'category__type__name', 'category__name']

    def __str__(self):
        return self.description

    def formatted_amount(self):
        return ('<div class="number">%s</div>' %
                (numberformat.numberformat(self.amount), ))

    formatted_amount.short_description = _('amount')
    formatted_amount.allow_tags = True

    def date_str(self):
        """
        Formats the date by "%Y-%m-%d." pattern.
        """
        return self.date.strftime("%Y-%m-%d")

    date_str.short_description = _("date")