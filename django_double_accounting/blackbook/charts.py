from datetime import timedelta, date

from .models import CurrencyConversion

import json


def get_color_code(i):
    color_codes = ["98, 181, 229", "134, 188, 37", "152, 38, 73", "124, 132, 131", "213, 216, 135", "247, 174, 248"]
    color = (i - 1) % len(color_codes)

    return color_codes[color]


class Chart:
    def __init__(self, data):
        self.data = data

    def generate_json(self):
        chart_data = self._generate_chart_data()
        chart_options = self._generate_chart_options()
        chart_data["options"] = chart_options

        return json.dumps(chart_data).replace('"<<', "").replace('>>"', "")

    def _generate_chart_data(self):
        raise NotImplementedError

    def _generate_chart_options(self):
        return self._get_default_options()

    def _get_default_options(self):
        return {
            "maintainAspectRatio": False,
            "legend": {
                "display": False,
            },
            "animation": {"duration": 0},
            "responsive": True,
            "tooltips": {
                "backgroundColor": "#f5f5f5",
                "titleFontColor": "#333",
                "bodyFontColor": "#666",
                "bodySpacing": 4,
                "xPadding": 12,
                "mode": "nearest",
                "intersect": 0,
                "position": "nearest",
            },
            "scales": {
                "yAxes": [
                    {
                        "barPercentage": 1.6,
                        "gridLines": {"drawBorder": False, "color": "rgba(225,78,202,0.1)", "zeroLineColor": "transparent"},
                        "ticks": {"padding": 20, "fontColor": "#9a9a9a"},
                    }
                ],
                "xAxes": [
                    {
                        "type": "time",
                        "time": {"unit": "day"},
                        "barPercentage": 1.6,
                        "gridLines": {"drawBorder": False, "color": "rgba(225,78,202,0.1)", "zeroLineColor": "transparent"},
                        "ticks": {"padding": 20, "fontColor": "#9a9a9a"},
                    }
                ],
            },
        }


class AccountChart(Chart):
    def __init__(self, data, accounts, start_date, end_date, *args, **kwargs):
        self.start_date = start_date
        self.end_date = end_date
        self.accounts = accounts

        super().__init__(data=data, *args, **kwargs)

    def _generate_chart_options(self):
        options = self._get_default_options()

        # options["tooltips"]["callbacks"] = {
        #     "label": "<<function(tooltipItems, data) { return data.datasets[tooltipItems.datasetIndex].label + ': ' + tooltipItems.yLabel + ' (%s)'; }>>"
        #     % get_currency(self.currency, self.user)
        # }

        if abs((self.end_date - self.start_date).days) > 150:
            options["scales"]["xAxes"][0]["time"]["unit"] = "week"

        return options

    def _generate_chart_data(self):
        dates = []

        for days_to_add in range(abs((self.end_date - self.start_date).days) + 1):
            day = self.start_date + timedelta(days=days_to_add)
            dates.append(day)

        data = {"type": "line", "data": {"labels": [date.strftime("%d %b %Y") for date in dates], "datasets": []}}

        accounts = {}

        for item in self.data:
            account_key = "{account} - {currency}".format(account=item.account.accountstring, currency=item.currency)

            if account_key in accounts.keys():
                accounts[account_key][item.journal_entry.date] = accounts[account_key].get(item.journal_entry.date, 0) + item.amount
            else:
                accounts[account_key] = {item.journal_entry.date: item.amount}

        for account in self.accounts:
            for currency in account.currencies.all():
                account_key = "{account} - {currency}".format(account=account.accountstring, currency=currency.code)

                if account_key not in accounts.keys():
                    accounts[account_key] = {}

            start_balance = account.balance_until_date(self.start_date - timedelta(days=1))
            for currency in start_balance:
                account_key = "{account} - {currency}".format(account=account.accountstring, currency=currency[1])

                if account_key in accounts.keys():
                    accounts[account_key][self.start_date] = accounts[account_key].get(self.start_date, 0) + currency[0]
                else:
                    accounts[account_key] = {self.start_date: currency[0]}

        counter = 1
        for account, date_entries in accounts.items():
            color = get_color_code(counter)
            counter += 1

            account_data = {
                "label": account,
                "fill": "!1",
                "borderColor": "rgba({color}, 1.0)".format(color=color),
                "borderWidth": 2,
                "borderDash": [],
                "borderDash0ffset": 0,
                "pointBackgroundColor": "rgba({color}, 1.0)".format(color=color),
                "pointBorderColor": "rgba(255,255,255,0)",
                "pointHoverBackgroundColor": "rgba({color}, 1.0)".format(color=color),
                "pointBorderWidth": 20,
                "pointHoverRadius": 4,
                "pointHoverBorderWidth": 15,
                "pointRadius": 4,
                "data": [],
            }

            if abs((self.end_date - self.start_date).days) > 150:
                account_data["pointRadius"] = 0

            for date_index in range(len(dates)):
                date = dates[date_index]
                value = 0

                if date_index != 0:
                    value = account_data["data"][date_index - 1]

                if date in date_entries.keys():
                    value += float(date_entries[date])

                account_data["data"].append(round(value, 2))
            data["data"]["datasets"].append(account_data)

        return data


class TransactionChart(Chart):
    def __init__(self, data, payee=False, expenses_budget=False, expenses_tag=False, *args, **kwargs):
        self.payee = payee
        self.expenses_budget = expenses_budget
        self.expenses_tag = expenses_tag

        super().__init__(data=data, *args, **kwargs)

    def _generate_chart_options(self):
        options = self._get_default_options()

        options["scales"] = {}
        options["legend"] = {"position": "right"}

        return options

    def _generate_chart_data(self):
        data = {
            "type": "pie",
            "data": {
                "labels": [],
                "datasets": [
                    {
                        "data": [],
                        "borderWidth": [],
                        "backgroundColor": [],
                        "borderColor": [],
                    },
                ],
            },
        }

        amounts = {}

        self.data = [item for item in self.data if item.amount < 0]

        for transaction in self.data:
            series_name = "Unknown - {currency}".format(currency=transaction.currency.code)

            if self.payee:
                if transaction.journal_entry.payee is not None:
                    series_name = "{name} - {currency}".format(name=transaction.journal_entry.payee, currency=transaction.currency.code)
                amounts[series_name] = amounts.get(series_name, 0) + float(transaction.amount)

            elif self.expenses_tag:
                for tag in transaction.journal_entry.tags.all():
                    series_name = "{name} - {currency}".format(name=tag, currency=transaction.currency.code)
                    amounts[series_name] = amounts.get(series_name, 0) + float(transaction.amount)

            elif self.expenses_budget:
                for budget in transaction.journal_entry.budgets.all():
                    series_name = "{name} - {currency}".format(name=budget.name, currency=budget.currency.code)
                    amounts[series_name] = amounts.get(series_name, 0) + float(
                        CurrencyConversion.convert(base_currency=transaction.currency, target_currency=budget.currency, amount=transaction.amount)
                    )

            else:
                amounts[series_name] = amounts.get(series_name, 0) + float(transaction.amount)

        counter = 1
        for series, amount in amounts.items():
            color = get_color_code(counter)
            counter += 1

            data["data"]["labels"].append(series)
            data["data"]["datasets"][0]["data"].append(round(amount, 2))
            data["data"]["datasets"][0]["borderWidth"].append(2)
            data["data"]["datasets"][0]["backgroundColor"].append("rgba({color}, 1.0)".format(color=color))
            data["data"]["datasets"][0]["borderColor"].append("rgba(255, 255, 255, 1.0)".format(color=color))

        return data
