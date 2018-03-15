# -*- coding: utf-8 -*
import tushare as ts
import pandas as pd
import time

balance_sheet_index = {
    'cash': 2,
    'bill_receivable': 5,
    'accounts_receivable': 6,
    'prepayments': 7,
    'inventory': 12,
    'total_current_assets': 18,
    'total_fixed_assets': 39,
    'total_assets': 40,
    'bill_payables': 44,
    'payables': 45,
    'total_current_liabilities': 58,
    'total_fixed_liabilities': 69,
    'total_liabilities': 70,
    'equity': 82
}
profit_statements_index = {
    'total_operating_income': 1,
    'total_operating_costs': 3,
    'operating_costs': 4,
    'net_profit': 20,
    'basic_per_share': 24

}
cash_flow_index = {
    'net_cash_flow_operating': 11
}


def retry_after_sleep(method):
    def wrapper(*arg, **kwargs):
        try:
            return method(*arg, **kwargs)
        except Exception as e:
            time.sleep(10)
            print("Try again after sleep.")
            return method(*arg, **kwargs)
    return wrapper


class Stocks(object):

    def __init__(self):
        self.stocks = {}
        self.profit_statements = None
        self.balance_sheets = None
        self.cash_flows = None
        self.years = ['20161231', '20151231', '20141231', '20131231', '20121231']
        self.actual_years = []

        self.total_asset_turnover = []
        self.accounts_receivable_turnover = []
        self.accounts_receivable_turnover_days = []
        self.inventory_turnover = []
        self.inventory_turnover_days = []

        self.net_profit_rate = []
        self.gross_margin = []
        self.basic_per_share = []

        self.cash_to_total_asset_ratio = []
        self.ar_to_total_asset_ratio = []
        self.payables_to_total_asset_ratio = []
        self.cash_flow_ratio = []
        self.net_cash_flow_operating = []

    def _clear_data(self):
        self.total_asset_turnover = []
        self.accounts_receivable_turnover = []
        self.accounts_receivable_turnover_days = []
        self.inventory_turnover = []
        self.inventory_turnover_days = []

        self.net_profit_rate = []
        self.gross_margin = []
        self.basic_per_share = []

        self.cash_to_total_asset_ratio = []
        self.ar_to_total_asset_ratio = []
        self.payables_to_total_asset_ratio = []
        self.cash_flow_ratio = []
        self.net_cash_flow_operating = []

    def _remove_st_stocks(self):
        #remove bank stocks

        self.stocks_not_st = {x: y for x, y in self.all_stocks.items() if 'ST' not in y}

    def _get_all_stocks(self):
        stocks = ts.get_stock_basics()
        indutries = {x: y for x, y in stocks['industry'].iteritems()}
        self.all_stocks = {x: y for x, y in stocks['name'].iteritems() if indutries[x] != '银行'}

    @retry_after_sleep
    def _get_actual_years(self, code):
        print(code)
        time.sleep(2)
        cash_flows = ts.get_cash_flow(code)
        time.sleep(2)
        if (cash_flows.shape[1] - 1) // 4 >= 5:
            self.actual_years = self.years[:]
        else:
            self.actual_years = self.years[:(cash_flows.shape[1] - 1) // 4]

    def _convert_to_float(self, series):
        return pd.to_numeric(series, downcast='float', errors='coerce')

    @retry_after_sleep
    def _make_cash_flows(self, code):
        cash_flows = ts.get_cash_flow(code)
        self.cash_flows = {year: self._convert_to_float(cash_flows[year]) for year in self.actual_years}

    @retry_after_sleep
    def _make_profit_statement(self, code):
        profits = ts.get_profit_statement(code)
        self.profit_statements = {year: self._convert_to_float(profits[year]) for year in self.actual_years}

    @retry_after_sleep
    def _make_balance_sheet(self, code):
        balances = ts.get_balance_sheet(code)
        self.balance_sheets = {year: self._convert_to_float(balances[year]) for year in self.actual_years}

    def _generate_analysis_data(self):
        for current_year, last_year in zip(self.actual_years, self.actual_years[1:] + [None]):
            income = self.profit_statements[current_year][profit_statements_index['total_operating_income']]
            cost = self.profit_statements[current_year][profit_statements_index['operating_costs']]
            total_assets = self.balance_sheets[current_year][balance_sheet_index['total_assets']]

            average_total_asset = self.balance_sheets[current_year][balance_sheet_index.get('total_assets')]
            average_accounts = self.balance_sheets[current_year][balance_sheet_index['bill_receivable']] +\
                               self.balance_sheets[current_year][balance_sheet_index['accounts_receivable']]
            average_inventory = self.balance_sheets[current_year][balance_sheet_index['inventory']]

            if last_year:
                average_total_asset = (self.balance_sheets[current_year][balance_sheet_index.get('total_assets')] +
                                       self.balance_sheets[last_year][balance_sheet_index.get('total_assets')]) / 2
                average_accounts = (self.balance_sheets[current_year][balance_sheet_index['bill_receivable']] +
                                    self.balance_sheets[current_year][balance_sheet_index['accounts_receivable']] +
                                    self.balance_sheets[last_year][balance_sheet_index['bill_receivable']] +
                                    self.balance_sheets[last_year][balance_sheet_index['accounts_receivable']]) / 2
                average_inventory = (self.balance_sheets[current_year][balance_sheet_index['inventory']] +
                                     self.balance_sheets[last_year][balance_sheet_index['inventory']]) / 2

            self.total_asset_turnover.append(income / average_total_asset)
            if average_accounts != 0:
                self.accounts_receivable_turnover.append(income / average_accounts)
                self.accounts_receivable_turnover_days.append(360 / (income / average_accounts))
            else:
                self.accounts_receivable_turnover.append(0)
                self.accounts_receivable_turnover_days.append(0)

            if average_inventory != 0:
                self.inventory_turnover.append(cost / average_inventory)
                self.inventory_turnover_days.append(360 / (cost / average_inventory))
            else:
                self.inventory_turnover.append(0)
                self.inventory_turnover_days.append(0)

            self.net_profit_rate.append(self.profit_statements[current_year][profit_statements_index['net_profit']] /
                                        income)
            self.gross_margin.append((income - cost) / income)
            self.basic_per_share.append(self.profit_statements[current_year][profit_statements_index['basic_per_share']])
            cash_equity = self.balance_sheets[current_year][balance_sheet_index['cash']] +\
                          self.balance_sheets[current_year][balance_sheet_index['prepayments']]
            self.cash_to_total_asset_ratio.append(cash_equity / total_assets)

            accounts = self.balance_sheets[current_year][balance_sheet_index['bill_receivable']] + \
                       self.balance_sheets[current_year][balance_sheet_index['accounts_receivable']]
            self.ar_to_total_asset_ratio.append(accounts / total_assets)
            payables = self.balance_sheets[current_year][balance_sheet_index['bill_payables']] + \
                       self.balance_sheets[current_year][balance_sheet_index['payables']]
            self.payables_to_total_asset_ratio.append(payables / total_assets)
            self.cash_flow_ratio.append(self.cash_flows[current_year][cash_flow_index['net_cash_flow_operating']] /
                                        self.balance_sheets[current_year][balance_sheet_index['total_current_liabilities']])
            self.net_cash_flow_operating.append(self.cash_flows[current_year][cash_flow_index['net_cash_flow_operating']])

    def _filter_by_esp(self):
        for ratio in self.cash_to_total_asset_ratio[0]:
            if ratio < 0.1:
                return False
        return True

    def _filter_by_esp(self):
        if self.basic_per_share[0] < 0.8:
                return False
        return True

    def _filter_by_cash_flow(self):
        for cash_flow in self.net_cash_flow_operating:
            if cash_flow < 0:
                return False
        return True

    def _filter_by_gpr_and_npr(self):
        return True

    def _filter(self):
        print(self.basic_per_share, self.net_cash_flow_operating, self.cash_to_total_asset_ratio)
        if not self._filter_by_cash_flow():
            return False
        if not self._filter_by_esp():
            return False
        if not self._filter_by_gpr_and_npr():
            return False
        return True

    def start_washing(self):
        self._get_all_stocks()
        self._remove_st_stocks()
        result = {}
        for code, name in self.stocks_not_st.items():
            self._clear_data()
            self._get_actual_years(code)
            self._make_balance_sheet(code)
            self._make_cash_flows(code)
            self._make_profit_statement(code)
            self._generate_analysis_data()
            if self._filter():
                result[code] = name
                print("The valuable stock is %s, %s"%(code, name))
        print(result)


if __name__ == '__main__':
    stock = Stocks()
    stock.start_washing()

