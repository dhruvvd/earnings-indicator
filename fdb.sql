CREATE TABLE IF NOT EXISTS companies (
    ticker VARCHAR(10),
    company_name VARCHAR(255),
    sector VARCHAR(100),
    industry VARCHAR(100),
    market_cap BIGINT,
    PRIMARY KEY (ticker),
    UNIQUE (ticker)
);

-- Seed tickers required by foreign keys (names filled optionally via OpenBB)
INSERT INTO companies (ticker) VALUES
    ('AAPL'), ('NVDA'), ('AVGO'), ('CRM'), ('AMD'), ('ADBE'), ('QCOM'),
    ('IBM'), ('NOW'), ('GOOG'), ('NFLX'), ('DIS'), ('F'),
    ('VZ'), ('T'), ('GME'), ('UBER'), ('DAL'), ('TXN'),
    ('DELL'), ('WDAY'), ('TGT'), ('GM'), ('LLY'), ('UNH'), ('JNJ'), ('ABBV'),
    ('MRK'), ('TMO'), ('ABT'), ('PFE'), ('AMGN'), ('ISRG'), ('SYK'), ('GILD'), ('VRTX'), ('AMZN'),
    ('TSLA'), ('WMT'), ('HD'), ('CMG'), ('LOW'), ('TJX'),
    ('KO'), ('PEP'), ('PM'), ('CL'), ('CAT'), ('BA'),
    ('UPS'), ('XOM'), ('CVX'), ('COP'), ('NEE'), ('EBAY')
ON CONFLICT (ticker) DO NOTHING;

CREATE TABLE IF NOT EXISTS financial_statements (
    id SERIAL,
    ticker VARCHAR(10),
    fiscal_period VARCHAR(10),  -- e.g., '2024-09-30' for Q3 2024
    period_type VARCHAR(2),  -- 'Q1', 'Q2', 'Q3', 'Q4'
    PRIMARY KEY (id),
    FOREIGN KEY (ticker) REFERENCES companies(ticker),

    -- Income Statement
    revenue DECIMAL(10,4),
    cost_of_revenue DECIMAL(10,4),
    gross_profit DECIMAL(10,4),
    operating_expenses DECIMAL(10,4),
    operating_income DECIMAL(10,4),
    net_income DECIMAL(10,4),
    eps DECIMAL(10,4),
    
    -- Balance Sheet
    total_assets DECIMAL(10,4),
    total_liabilities DECIMAL(10,4),
    total_equity DECIMAL(10,4),
    current_assets DECIMAL(10,4),
    current_liabilities DECIMAL(10,4),
    cash DECIMAL(10,4),
    total_debt DECIMAL(10,4),
    
    -- Cash Flow
    operating_cash_flow DECIMAL(10,4),
    capex DECIMAL(10,4),
    free_cash_flow DECIMAL(10,4)
);

CREATE TABLE IF NOT EXISTS analyst_estimates (
    id SERIAL,
    ticker VARCHAR(10),
    fiscal_period VARCHAR(10),
    consensus_eps DECIMAL(10,4),
    num_analysts INT,
    eps_high DECIMAL(10,4),
    eps_low DECIMAL(10,4),
    PRIMARY KEY (id),
    FOREIGN KEY (ticker) REFERENCES companies(ticker)
);

CREATE TABLE IF NOT EXISTS features  (
    id SERIAL,
    ticker VARCHAR(10),
    fiscal_period VARCHAR(10),

    -- features

    -- growth metrics
    qoq_rev DECIMAL(10, 4),
    yoy_rev DECIMAL(10, 4),
    qoq_eps DECIMAL(10, 4),
    yoy_eps DECIMAL(10, 4),
    momentum DECIMAL(10, 4),

    -- profitability ratios
    net_margin DECIMAL(10, 4),
    gross_margin DECIMAL(10, 4),
    oper_margin DECIMAL(10, 4),
    roe DECIMAL(10, 4),

    -- balance sheet health
    de_ratio DECIMAL(10, 4),
    current_ratio DECIMAL(10, 4),
    cash_ratio DECIMAL(10, 4),

    -- efficiency metrics
    asset_turn DECIMAL(10, 4),

    -- historical patterns
    eps_status VARCHAR(10),
    eps_surprise DECIMAL(10, 4),

    PRIMARY KEY (id),
    FOREIGN KEY (ticker) REFERENCES companies(ticker)
);
