from django import forms
from expense.models import Expense


class DateInput(forms.DateInput):
    input_type = 'date'


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['user', 'date', 'category', 'description', 'amount']
        widgets = {
            'date': DateInput()
        }