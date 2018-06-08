# -*- coding: utf-8 -*
import tushare as ts
import pandas as pd
import time
import sys
from sqlalchemy import *

reload(sys)
sys.setdefaultencoding('utf-8')


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

    log_file = "/root/db.log"

    def __init__(self):
        self.counter = 1
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

        self.debt_to_assets_ratio = []

    def _remove_st_stocks(self):
        #remove bank stocks

        self.stocks_not_st = {x: y for x, y in self.all_stocks.items() if 'ST' not in y}

    def _get_all_stocks(self):
        stocks = ts.get_stock_basics()
        indutries = {x: y for x, y in stocks['industry'].iteritems()}
        self.all_stocks = {x: y for x, y in stocks['name'].iteritems() if indutries[x] not in ['银行', '证券', '保险']}

    def _convert_to_float(self, series):
        return pd.to_numeric(series, downcast='float', errors='coerce')

    @retry_after_sleep
    def _make_cash_flows(self, code, engine):
        cash_flows = ts.get_cash_flow(code)
        cfes = cash_flows.T
        col_name = cfes.columns.tolist()
        col_name.insert(0, 'code')
        result = cfes.reindex(columns=col_name, fill_value=code)
        result.index.name = 'date'
        result.to_sql('consolidated_cash_flow_statement', engine, if_exists='append',
                      dtype={'date': VARCHAR(50)})

    @retry_after_sleep
    def _make_profit_statement(self, code, engine):
        profits = ts.get_profit_statement(code)
        pfs = profits.T
        col_name = pfs.columns.tolist()
        col_name.insert(0, 'code')
        result = pfs.reindex(columns=col_name, fill_value=code)
        result.index.name = 'date'
        result.to_sql('consolidated_income_statement', engine, if_exists='append',
                      dtype={'date': VARCHAR(50)})



    @retry_after_sleep
    def _make_balance_sheet(self, code, engine):
        balances = ts.get_balance_sheet(code)
        bses = balances.T
        col_name = bses.columns.tolist()
        col_name.insert(0, 'code')
        result = bses.reindex(columns=col_name, fill_value=code)
        result.index.name = 'date'
        result.to_sql('consolidated_balance_sheet', engine, if_exists='append',
                      dtype={'date': VARCHAR(50)})

    def write_messages_to_logfile(self, messages):
        with open(self.log_file, 'a+') as log:
            log.write("%s" % (messages + '\n'))

    def get_codes(self):
        try:
            with open(self.log_file, 'r') as log:
                return log.readlines()
        except IOError:
            return []

    def start_washing(self):

        self._get_all_stocks()
        self._remove_st_stocks()

        engine = create_engine('mysql+pymysql://root:sxkj1111@123.56.94.158/frank?charset=utf8')
        for code, name in self.stocks_not_st.items():
            if (code + '\n') in self.get_codes():
                self.counter = self.counter + 1
                continue
            print("This is the %dth stock, code is %s" % (self.counter, code))
            # self._make_balance_sheet(code, engine)
            # self._make_cash_flows(code, engine)
            self._make_profit_statement(code, engine)
            self.write_messages_to_logfile(code)
            self.counter = self.counter + 1


if __name__ == '__main__':
    stock = Stocks()
    stock.start_washing()
