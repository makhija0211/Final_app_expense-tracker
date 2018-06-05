from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse
from django.db.models import Sum
from django.template import Context, loader
from django.utils.translation import ugettext_lazy as _
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from expense.forms import ExpenseForm
from django.template.context_processors import csrf
from datetime import datetime
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required
import expense.models as models


def _get_add_form(request):
    form = ExpenseForm()
    form.base_fields["user"].initial = request.user.id
    form.base_fields["date"].initial = datetime.now().strftime("%Y-%m-%d")
    form.fields["category"].queryset = models.Category.objects.exclude(
        id__in=models.HiddenCategory.objects.filter(
            user__id=request.user.id).values_list("category__id",
                                                  flat=True)).order_by(
                                                      "type__name", "name")

    return form


@csrf_protect
@never_cache
@login_required
def add(request):
    t = loader.get_template('add.html')
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _("The expense was added successfully"))
            form = _get_add_form(request)

    else:
        form = _get_add_form(request)

    c = Context({
        'form': form,
        'messages': messages.get_messages(request),
        'userid': request.user.id
    })
    c.update(csrf(request))
    response = HttpResponse(t.render(c))
    return response


@login_required
def log(request):
    t = loader.get_template('log.html')
    items = models.Expense.objects.all().order_by("-id")
    paginator = Paginator(items, 10)

    page = request.GET.get("page")
    try:
        expenses = paginator.page(page)
    except PageNotAnInteger:
        expenses = paginator.page(1)
    except EmptyPage:
        expenses = paginator.page(paginator.num_pages)

    c = Context({
        'messages': messages.get_messages(request),
        'expenses': expenses
    })
    c.update(csrf(request))
    return HttpResponse(t.render(c))


@never_cache
@login_required
def monthly(request):
    t = loader.get_template('monthly.html')
    month_list = models.Expense.objects.get_months()
    paginator = Paginator(month_list, 1)

    page = request.GET.get("page")
    try:
        months = paginator.page(page)
    except PageNotAnInteger:
        months = paginator.page(1)
    except EmptyPage:
        months = paginator.page(paginator.num_pages)

    items = months.object_list

    current_month = items[:1]
    if current_month:
        expenses = models.Expense.objects.filter(
            date__year=current_month[0].year,
            date__month=current_month[0].month)

        data_category = expenses.values(
            "category__type__name", "category__name").annotate(
                Sum("amount")).order_by(
                    "category__type__name", "category__name")

#       extend with order 0, to have the subtotals at the end
        data_category = [dict({'subtotal': False}, **item) for item in
                         data_category]

        data_type = expenses.values("category__type__name").annotate(
            Sum("amount")).order_by("category__type__name")

        data_type = [dict({"category__name": "Total", "subtotal": True}, **item)
                     for item in data_type]

        data = list(data_category) + list(data_type)

#       sort the result by, type_name, order, category_name
        data = sorted(data, key=lambda x: (x["category__type__name"],
                                           x["subtotal"],
                                           x["category__name"]))

    c = Context({
        'messages': messages.get_messages(request),
        'months': months,
        'data': data,
        'current_month': current_month[0],
    })
    c.update(csrf(request))
    return HttpResponse(t.render(c))