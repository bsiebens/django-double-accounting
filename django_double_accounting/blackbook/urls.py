from django.urls import path

from .views import dashboard, profile, accounts, transactions

app_name = "blackbook"
urlpatterns = [
    path("", dashboard.dashboard, name="dashboard"),
    path("profile/", profile.profile, name="profile"),
    path("accounts/add/", accounts.add_edit, name="accounts_add"),
    path("accounts/edit/<str:uuid>/", accounts.add_edit, name="accounts_edit"),
    path("accounts/delete/", accounts.delete, name="accounts_delete"),
    path("accounts/<str:account_type>/", accounts.view, name="accounts_list"),
    path("accounts/<str:account_type>/<str:uuid>/", accounts.view, name="accounts_view"),
    path("transactions/add/", transactions.add_edit, name="transactions_add"),
    path("transactions/edit/<str:uuid>/", transactions.add_edit, name="transactions_edit"),
    path("transactions/delete/", transactions.delete, name="transactions_delete"),
    path("transactions/", transactions.view, name="transactions_list"),
]
