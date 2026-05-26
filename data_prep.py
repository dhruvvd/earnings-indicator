import os

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()
engine = create_engine(os.environ["DATABASE_URL"])
findata = pd.read_sql("""
    SELECT  ae.ticker, 
            ae.fiscal_period, 
            f.qoq_rev,
            f.yoy_rev,
            f.qoq_eps,
            f.yoy_eps,
            f.momentum,
            f.net_margin,
            f.gross_margin,
            f.oper_margin,
            f.roe,
            f.de_ratio,
            f.current_ratio,
            f.cash_ratio,
            f.asset_turn,
            f.eps_status,
            f.eps_surprise
    FROM analyst_estimates ae
    RIGHT JOIN features f
    ON RIGHT(ae.fiscal_period, 4) = RIGHT(f.fiscal_period, 4)
    AND LEFT(ae.fiscal_period, 2) = LEFT(f.fiscal_period, 2)
    AND ae.ticker = f.ticker
    ORDER BY ticker, RIGHT(f.fiscal_period, 4) ASC, LEFT(f.fiscal_period, 2) ASC;""", 
engine)

findata.loc[findata['eps_surprise'] > 0, 'eps_status'] = 1
findata.loc[findata['eps_surprise'] < 0, 'eps_status'] = 0

findata['eps_status'] = findata['eps_status'].astype('Float64')

findata.to_csv("data/findata.csv", index=False)

"""
train = findata.loc[findata['fiscal_period'].str.contains("2021") | findata['fiscal_period'].str.contains("2022")]
val = findata.loc[findata['fiscal_period'].str.contains("2023")]
test = findata.loc[findata['fiscal_period'].str.contains("2024")]

train.to_csv("train.csv", index=False)
val.to_csv("val.csv", index=False)
test.to_csv("test.csv", index=False)
"""