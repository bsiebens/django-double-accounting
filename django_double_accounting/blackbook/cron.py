from django.utils import timezone

from .models import Budget
from .utilities import calculate_period


def create_budget_period():
    budgets = (
        Budget.objects.filter(is_active=True)
        .exclude(auto_budget=Budget.AutoBudget.NO)
        .filter(periods__end_date__lt=timezone.localdate())
        .exclude(periods__start_date__lte=timezone.localdate(), periods__end_date__gte=timezone.localdate())
    )

    for budget in budgets:
        amount_to_add = budget.amount

        if budget.auto_budget == Budget.AutoBudget.ADD:
            amount_to_add += budget.budgetperiods.last().available

        period = calculate_period(periodicity=budget.period, start_date=timezone.localdate())
        budget.budgetperiods.create(start_date=period["start_date"], end_date=period["end_date"], amount=amount_to_add)
