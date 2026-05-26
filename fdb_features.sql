-- Run after scrape.py loads financial_statements and analyst_estimates.
-- Safe to re-run: clears and rebuilds the features table.

DELETE FROM features;

INSERT INTO features (ticker, fiscal_period)
SELECT
    ticker,
    fiscal_period
FROM financial_statements;

-- QoQ revenue calculator
WITH qrt AS (
    SELECT fiscal_period, ticker, revenue, prev_quarter_rev, ((revenue - prev_quarter_rev) / prev_quarter_rev) * 100 AS qoq_rev
    FROM (
        SELECT fiscal_period, ticker, revenue,
        LAG(revenue)
        OVER (PARTITION BY ticker ORDER BY RIGHT(fiscal_period, 4) ASC, LEFT(fiscal_period, 2) ASC) AS prev_quarter_rev
        FROM financial_statements
    ) financial_statements
)
UPDATE features f
SET qoq_rev = qrt.qoq_rev
FROM qrt
WHERE f.ticker = qrt.ticker AND f.fiscal_period = qrt.fiscal_period;

-- YoY revenue calculator
WITH yrt AS (
    SELECT fiscal_period, ticker, revenue, prev_quarter_rev, ((revenue - prev_quarter_rev) / prev_quarter_rev) * 100 AS yoy_rev
    FROM (
        SELECT fiscal_period, ticker, revenue,
        LAG(revenue, 4)
        OVER (PARTITION BY ticker ORDER BY RIGHT(fiscal_period, 4) ASC, LEFT(fiscal_period, 2) ASC) AS prev_quarter_rev
        FROM financial_statements
    ) financial_statements
)
UPDATE features f
SET yoy_rev = yrt.yoy_rev
FROM yrt
WHERE f.ticker = yrt.ticker AND f.fiscal_period = yrt.fiscal_period;

-- QoQ consensus eps calculator
-- DISCLAIMER: changed GME, XOM, COP consensus_eps to 0.001 to avoid division by 0
WITH qce AS (
    SELECT fiscal_period, ticker, consensus_eps, prev_eps, ((consensus_eps - prev_eps) / prev_eps) * 100 as qoq_eps
    FROM (
        SELECT fiscal_period, ticker, consensus_eps,
        LAG(consensus_eps)
        OVER (PARTITION BY ticker ORDER BY RIGHT(fiscal_period, 4) ASC, LEFT(fiscal_period, 2) ASC) AS prev_eps
        FROM analyst_estimates
    ) analyst_estimates
)
UPDATE features f
SET qoq_eps = qce.qoq_eps
FROM qce
WHERE f.ticker = qce.ticker AND f.fiscal_period = qce.fiscal_period;

-- YoY consensus eps calculator
WITH yce AS (
    SELECT fiscal_period, ticker, consensus_eps, prev_eps, ((consensus_eps - prev_eps) / prev_eps) * 100 as yoy_eps
    FROM (
        SELECT fiscal_period, ticker, consensus_eps,
        LAG(consensus_eps, 4)
        OVER (PARTITION BY ticker ORDER BY RIGHT(fiscal_period, 4) ASC, LEFT(fiscal_period, 2) ASC) AS prev_eps
        FROM analyst_estimates
    ) analyst_estimates
)
UPDATE features f
SET yoy_eps = yce.yoy_eps
FROM yce
WHERE f.ticker = yce.ticker AND f.fiscal_period = yce.fiscal_period;

-- momentum calculator
WITH mom_calc AS (
    WITH yoy_calc (fiscal_period, ticker, revenue, prev_quarter_rev)
    AS (
        SELECT fiscal_period, ticker, revenue,
        LAG(revenue, 4)
        OVER (PARTITION BY ticker ORDER BY RIGHT(fiscal_period, 4) ASC, LEFT(fiscal_period, 2) ASC) AS prev_quarter_rev
        FROM financial_statements 
        ORDER BY ticker, RIGHT(fiscal_period, 4) ASC, LEFT(fiscal_period, 2) ASC
    ),
    momentum 
    AS (
        SELECT fiscal_period, 
        ticker, 
        ((revenue - prev_quarter_rev) / prev_quarter_rev) * 100 as yoy
        FROM yoy_calc
    )
    SELECT fiscal_period, ticker, yoy -
    LAG (YoY, 4)
    OVER (PARTITION BY ticker ORDER BY RIGHT(fiscal_period, 4) ASC, LEFT(fiscal_period, 2) ASC) as momentum
    FROM momentum
    ORDER BY ticker, RIGHT(fiscal_period, 4) ASC, LEFT(fiscal_period, 2) ASC
)
UPDATE features f
SET momentum = mom_calc.momentum
FROM mom_calc
WHERE f.ticker = mom_calc.ticker AND f.fiscal_period = mom_calc.fiscal_period;

-- net margin calculator
WITH nm AS (
    SELECT ticker, fiscal_period, (net_income / revenue) * 100 as net_margin
    FROM financial_statements
)
UPDATE features f
SET net_margin = nm.net_margin
FROM nm
WHERE f.ticker = nm.ticker AND f.fiscal_period = nm.fiscal_period;

-- gross margin calculator
WITH gm AS (
    SELECT ticker, fiscal_period, (gross_profit / revenue) * 100 as gross_margin
    FROM financial_statements
)
UPDATE features f
SET gross_margin = gm.gross_margin
FROM gm
WHERE f.ticker = gm.ticker AND f.fiscal_period = gm.fiscal_period;

-- operating margin calculator
WITH om AS (
    SELECT ticker, fiscal_period, (operating_income / revenue) * 100 as oper_margin
    FROM financial_statements
)
UPDATE features f
SET oper_margin = om.oper_margin
FROM om
WHERE f.ticker = om.ticker AND f.fiscal_period = om.fiscal_period;

-- roe calculator
WITH roe_c AS (
    SELECT ticker, fiscal_period, (net_income / (total_assets - total_liabilities)) * 100 AS roe
    FROM financial_statements
)
UPDATE features f
SET roe = roe_c.roe
FROM roe_c
WHERE f.ticker = roe_c.ticker AND f.fiscal_period = roe_c.fiscal_period;

-- d/e ratio calculator
WITH de AS (
    SELECT ticker, fiscal_period, (total_liabilities / (total_assets - total_liabilities)) as de_ratio
    FROM financial_statements
)
UPDATE features f
SET de_ratio = de.de_ratio
FROM de
WHERE f.ticker = de.ticker AND f.fiscal_period = de.fiscal_period;

-- current ratio calculator
WITH cr AS (
    SELECT ticker, fiscal_period, (current_assets / current_liabilities) as current_ratio
    FROM financial_statements
)
UPDATE features f
SET current_ratio = cr.current_ratio
FROM cr
WHERE f.ticker = cr.ticker AND f.fiscal_period = cr.fiscal_period;

-- cash ratio calculator
WITH cash AS (
    SELECT ticker, fiscal_period, (cash / current_liabilities) as cash_ratio
    FROM financial_statements
)
UPDATE features f
SET cash_ratio = cash.cash_ratio
FROM cash
WHERE f.ticker = cash.ticker AND f.fiscal_period = cash.fiscal_period;

-- asset turnover calculator
WITH atc AS (
    SELECT ticker, fiscal_period, (revenue / total_assets) as asset_turn
    FROM financial_statements
)
UPDATE features f
SET asset_turn = atc.asset_turn
FROM atc
WHERE f.ticker = atc.ticker AND f.fiscal_period = atc.fiscal_period;

-- beat/miss
WITH bm AS (
    WITH eps_compare (ticker, fiscal_period, eps, consensus_eps)
    AS (
        SELECT financial_statements.ticker, financial_statements.fiscal_period, financial_statements.eps, analyst_estimates.consensus_eps
        FROM financial_statements
        JOIN analyst_estimates
        ON financial_statements.id = analyst_estimates.id
    )
    SELECT ticker, fiscal_period,
    CASE 
        WHEN eps > consensus_eps THEN 'beat'
        ELSE 'miss'
    END AS eps_status
    FROM eps_compare
)
UPDATE features f
SET eps_status = bm.eps_status
FROM bm
WHERE f.ticker = bm.ticker AND f.fiscal_period = bm.fiscal_period;

-- eps surprise number (just % difference)
WITH esn AS (
    WITH eps_compare (ticker, fiscal_period, eps, consensus_eps)
    AS (
        SELECT financial_statements.ticker, financial_statements.fiscal_period, financial_statements.eps, analyst_estimates.consensus_eps
        FROM financial_statements
        JOIN analyst_estimates
        ON financial_statements.id = analyst_estimates.id
    )
    SELECT ticker, fiscal_period, eps, consensus_eps, ((eps - consensus_eps) / consensus_eps) * 100 as eps_surprise
    FROM eps_compare
)
UPDATE features f
SET eps_surprise = esn.eps_surprise
FROM esn
WHERE f.ticker = esn.ticker AND f.fiscal_period = esn.fiscal_period;
