import pandas as pd
from openbb import obb
from openbb_core.provider.standard_models.analyst_estimates import (
    AnalystEstimatesData,
    AnalystEstimatesQueryParams,
)
import openpyxl
from sqlalchemy import create_engine, Integer, BigInteger, String, Float
import warnings
import os
from dotenv import load_dotenv

load_dotenv()
warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")
engine = create_engine(os.environ["DATABASE_URL"])

tickers = [
    "AAPL", "NVDA", "AVGO", "CRM", "AMD", "ADBE", "QCOM", 
    "IBM", "NOW", "GOOG", "NFLX", "DIS", "F",
    "VZ", "T", "GME", "UBER", "DAL", "TXN",
    "DELL", "WDAY", "TGT", "GM", "LLY", "UNH", "JNJ", "ABBV",
    "MRK", "TMO", "ABT", "PFE", "AMGN", "ISRG", "SYK", "GILD", "VRTX", "AMZN",
    "TSLA", "WMT", "HD", "CMG", "LOW", "TJX",
    "KO", "PEP", "PM", "CL", "CAT", "BA",
    "UPS", "XOM", "CVX", "COP", "NEE", "EBAY"
]

#all table values in millions of dollars for financial statements
"""
mapping = {
    "ticker": String(10),
    "company_name": String(255),
    "sector": String(100),
    "industry": String(100),
    "market_cap": BigInteger
}
def company_info():
    company_dict = {'ticker': [], "company_name": [], "sector": [], "industry": [], "market_cap": []}

    for ticker in tickers:
        comp_info = obb.equity.profile(symbol=ticker)
        results = comp_info.results[0]
        company_dict['ticker'].append(ticker)
        company_dict['company_name'].append(results.name)
        company_dict['sector'].append(results.sector)
        company_dict['industry'].append(results.industry_category)
        company_dict['market_cap'].append(results.market_cap)

    company_df = pd.DataFrame(company_dict)

    return company_df
company_df = company_info()
company_df.to_sql(
    name='companies',
    con=engine,
    if_exists='append',
    index=False,
    dtype=mapping
)

mapping = {
    "ticker": String(10),
    "fiscal_period": String(10),
    "period_type": String(2),

    "revenue": Float,
    "cost_of_revenue": Float,
    "gross_profit": Float,
    "operating_expenses": Float,
    "operating_income": Float,
    "net_income": Float,
    "eps": Float,

    "total_assets": Float,
    "total_liabilities": Float,
    "total_equity": Float,
    "current_assets": Float,
    "current_liabilities": Float,
    "cash": Float,
    "total_debt": Float,

    "operating_cash_flow": Float,
    "capex": Float,
    "free_cash_flow": Float
}
def income_reader():
    total_income = pd.DataFrame()

    for ticker in tickers:
        income = pd.read_excel(f"stock_statements/{ticker}/{ticker}_PL.xlsx")
        fund = pd.read_excel(f"stock_statements/{ticker}/{ticker}_DERIVED.xlsx")

        income.rename(columns={"Unnamed: 0": "Metrics"}, inplace=True)
        income.dropna(inplace=True)

        fund = fund.loc[[5]]
        income = income._append(fund)
        income.drop(columns=['Unnamed: 0'], inplace=True)
        income.loc[5, 'Metrics'] = 'eps'

        metrics = ['Revenue', 'Cost of revenue', 'Gross Profit', 'Operating Expenses', 'Operating Income', 'Net Income', 'eps']
        pattern = '|'.join(metrics)
        income = income[income['Metrics'].str.contains(pattern, case=False, na=False)]
        income.set_index('Metrics', inplace=True)
        income = income.T

        income.loc[income.index.str.contains('Q1'), 'period_type'] = 'Q1'
        income.loc[income.index.str.contains('Q2'), 'period_type'] = 'Q2'
        income.loc[income.index.str.contains('Q3'), 'period_type'] = 'Q3'
        income.loc[income.index.str.contains('Q4'), 'period_type'] = 'Q4'

        income['ticker'] = ticker

        mapping = {
            'Revenue': 'revenue',
            'Cost of revenue': 'cost_of_revenue',
            'Gross Profit': 'gross_profit',
            'Operating Expenses': 'operating_expenses',
            'Operating Income (Loss)': 'operating_income',
            'Net Income': 'net_income'
        }   
        income.rename(inplace=True, columns=mapping)

        order = ['ticker', 'period_type', 'revenue', 'cost_of_revenue',
                'gross_profit', 'operating_expenses', 'operating_income', 'net_income',
                'eps']

        income = income[order]

        income.reset_index(inplace=True)
        income.rename(inplace=True, columns={'index': "fiscal_period"})
        income.columns.name = None

        total_income = pd.concat([total_income, income], ignore_index=True)

    return total_income
def balance_reader():
    total_balance = pd.DataFrame()

    for ticker in tickers:
        balance = pd.read_excel(f"stock_statements/{ticker}/{ticker}_BS.xlsx")
        fund = pd.read_excel(f"stock_statements/{ticker}/{ticker}_DERIVED.xlsx")

        balance.rename(columns={"Unnamed: 0": "Metrics"}, inplace=True)
        balance.dropna(inplace=True)

        fund = fund.loc[[29]]
        balance = balance._append(fund)
        balance.drop(columns=['Unnamed: 0'], inplace=True)
        balance.loc[29, 'Metrics'] = "Total Debt"

        metrics = ["Total Assets", "Total Liabilities", "Total Equity", "Total Current Assets", "Total Current Liabilities", "Cash & Cash Equivalents", "Total Debt"]
        pattern = '|'.join(metrics)
        balance = balance[balance['Metrics'].str.contains(pattern, case=False, na=False)]
        balance.set_index('Metrics', inplace=True)
        balance = balance.T

        balance['ticker'] = ticker

        mapping = {
            "Total Assets": "total_assets",
            "Total Liabilities": "total_liabilities",
            "Total Equity": "total_equity",
            "Total Current Assets": "current_assets",
            "Total Current Liabilities": "current_liabilities",
            "Cash & Cash Equivalents": "cash",
            "Total Debt": "total_debt"
        }

        balance.rename(inplace=True, columns=mapping)
        order = ["ticker", "total_assets", "total_liabilities", "total_equity", "current_assets", "current_liabilities", "cash", "total_debt"]
        balance = balance[order]

        balance.reset_index(inplace=True)
        balance.rename(inplace=True, columns={'index': "fiscal_period"})
        balance.columns.name = None

        total_balance = pd.concat([total_balance, balance], ignore_index=True)

    return total_balance
def cash_reader():
    total_cash = pd.DataFrame()

    for ticker in tickers:
        cash = pd.read_excel(f"stock_statements/{ticker}/{ticker}_CF.xlsx")
        fund = pd.read_excel(f"stock_statements/{ticker}/{ticker}_DERIVED.xlsx")

        cash.rename(inplace=True, columns={"Unnamed: 0": "Metrics"})
        cash.dropna(inplace=True)
        fund = fund.loc[[10]]
        cash = cash._append(fund)
        cash.drop(columns=['Unnamed: 0'], inplace=True)
        cash.loc[10, 'Metrics'] = "free_cash_flow"

        metrics = ["Cash from Operating Activities", "free_cash_flow"]
        pattern = '|'.join(metrics)
        cash = cash[cash['Metrics'].str.contains(pattern, case=False, na=False)]
        cash.set_index('Metrics', inplace=True)
        cash = cash.T

        cash['ticker'] = ticker

        cash.rename(inplace=True, columns={"Cash from Operating Activities": "operating_cash_flow"})
        cash['capex'] = 0
        cash = cash[["ticker", "operating_cash_flow", "capex", "free_cash_flow"]]

        cash.reset_index(inplace=True)
        cash.rename(inplace=True, columns={'index': "fiscal_period"})
        cash.columns.name = None

        total_cash = pd.concat([total_cash, cash], ignore_index=True)

    return total_cash

income_statement = income_reader()
balance_statement = balance_reader()
cash_statement = cash_reader()

merged_one = income_statement.merge(balance_statement, on=["fiscal_period", "ticker"], how="inner")
financial_statements = merged_one.merge(cash_statement, on=["fiscal_period", "ticker"], how="inner")
financial_statements["capex"] = financial_statements["operating_cash_flow"] - financial_statements["free_cash_flow"]

financial_statements.loc[financial_statements['fiscal_period'].str.contains("Q1"), 'quarter'] = 1
financial_statements.loc[financial_statements['fiscal_period'].str.contains("Q2"), 'quarter'] = 2
financial_statements.loc[financial_statements['fiscal_period'].str.contains("Q3"), 'quarter'] = 3
financial_statements.loc[financial_statements['fiscal_period'].str.contains("Q4"), 'quarter'] = 4

financial_statements.loc[financial_statements['fiscal_period'].str.contains("2019"), 'year'] = 2019
financial_statements.loc[financial_statements['fiscal_period'].str.contains("2020"), 'year'] = 2020
financial_statements.loc[financial_statements['fiscal_period'].str.contains("2021"), 'year'] = 2021
financial_statements.loc[financial_statements['fiscal_period'].str.contains("2022"), 'year'] = 2022
financial_statements.loc[financial_statements['fiscal_period'].str.contains("2023"), 'year'] = 2023
financial_statements.loc[financial_statements['fiscal_period'].str.contains("2024"), 'year'] = 2024

financial_statements = financial_statements.sort_values(['ticker', 'year', 'quarter'])
financial_statements = financial_statements.drop(columns=['year', 'quarter'])

financial_statements.to_sql(
    name='financial_statements',
    con=engine,
    if_exists='append',
    index=False,
    dtype=mapping
)
eps_history = pd.read_csv("stock_statements/eps_history.csv")

mapping = {
    "ticker": String(10),
    "fiscal_period": String(10),
    "consensus_eps": Float,
    "num_analysts": Float,
    "eps_high": Float,
    "eps_low": Float
}
def estimate_reader():
    estimates = pd.DataFrame()

    for ticker in tickers:
        eps_estimate = pd.read_csv("stock_statements/eps_estimate.csv")

        eps_estimate.drop(inplace=True, columns=['date', 'recent', 'year_ago'])
        eps_est = eps_estimate.loc[(eps_estimate['act_symbol'] == ticker) & (eps_estimate['period'] == 'Current Quarter') & (eps_estimate['period_end_date'] > "2018-12-31") &                    (eps_estimate['period_end_date'] < "2025-01-31")]
        eps_est = eps_est.drop_duplicates(subset=['period_end_date'], keep='first')
        eps_est.drop(inplace=True, columns=['period'])
        eps_est.rename(inplace=True, columns={"act_symbol": "ticker", "count": "num_analysts", "high": "eps_high", "low": "eps_low", "consensus": "consensus_eps"})

        eps_est['period_end_date'] = pd.to_datetime(eps_est['period_end_date'])
        eps_est['year'] = eps_est['period_end_date'].dt.year
        eps_est['quarter_num'] = (eps_est.groupby('year').cumcount() + 1).astype(str)
        eps_est['quarter'] = 'Q' + eps_est['quarter_num'].astype(str) + " " + eps_est['year'].astype(str)
        eps_est.drop(inplace=True, columns=['period_end_date', 'year', 'quarter_num'])
        eps_est.rename(inplace=True, columns={"quarter": "fiscal_period"})

        order = ['ticker', 'fiscal_period', 'consensus_eps', 'num_analysts', 'eps_high', 'eps_low']
        eps_est = eps_est[order]

        estimates = pd.concat([estimates, eps_est], ignore_index=True)

    return estimates
estimates = estimate_reader()

estimates.to_sql(
    name='analyst_estimates',
    con=engine,
    if_exists='append',
    index=False,
    dtype=mapping
)
"""