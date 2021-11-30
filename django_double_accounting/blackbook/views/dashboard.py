from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from ..charts import AccountChart


@login_required
def dashboard(request):
    return render(request, "blackbook/dashboard.html")
