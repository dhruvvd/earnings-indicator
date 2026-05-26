# earnings-indicator

Predict EPS beat/miss (`eps_status`) from quarterly financial features using PyTorch models.

## Prerequisites

- Python 3.12
- PostgreSQL 14+ (local install; Homebrew on macOS works well)
- [Git LFS](https://git-lfs.com/) (required for the large raw data file)

## Setup

```bash
git clone https://github.com/dhruvvd/earnings-indicator.git
cd earnings-indicator
git lfs install
git lfs pull

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env with your PostgreSQL connection string (see below)
```

### PostgreSQL (macOS / Homebrew)

This project expects a local database named `findata`. [`fdb.sql`](fdb.sql) creates the tables and feature-engineering SQL used by the pipeline.

Install and start PostgreSQL:

```bash
brew install postgresql@18
brew services start postgresql@18
```

Add `psql` to your PATH if Homebrew prompts you to (it prints the exact command after install).

Create a database and user, then load the schema:

```bash
# Open a psql shell as your macOS user (default Homebrew superuser)
psql postgres

# Inside psql:
CREATE DATABASE findata;
CREATE USER your_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE findata TO your_user;
\q

# Apply schema (run from the repo root)
psql -d findata -f fdb.sql
```

Set `.env` to match your credentials:

```
DATABASE_URL=postgresql+psycopg2://your_user:your_password@localhost:5432/findata
```

On Linux or Windows, use your distro's PostgreSQL install instead of Homebrew; the `CREATE DATABASE` / `psql -f fdb.sql` steps are the same.

You only need to run `fdb.sql` once on a fresh database. Re-running `scrape.py` repopulates the tables.

## Pipeline

```
stock_statements/  →  scrape.py  →  PostgreSQL (findata)
fdb.sql            →  feature SQL in DB
data_prep.py       →  data/findata.csv
modelv1.ipynb      →  feedforward classifier (train/val/test splits)
modelv2.ipynb      →  LSTM sequence model
```

Run the ETL and export:

```bash
python scrape.py
python data_prep.py
```

Open `modelv1.ipynb` or `modelv2.ipynb` in Jupyter to train and evaluate models.

## Data

| Path | Description |
|------|-------------|
| `stock_statements/` | Raw Excel financial statements per ticker + EPS estimate/history CSVs |
| `data/findata.csv` | Joined feature matrix exported from PostgreSQL |
| `data/train.csv`, `val.csv`, `test.csv` | Train/validation/test splits for modelv1 |

`stock_statements/eps_estimate.csv` (~416 MB) is stored via Git LFS.

## Features

13 financial features per ticker/quarter: QoQ/YoY revenue and EPS growth, momentum, net/gross/operating margins, ROE, debt-to-equity, current ratio, cash ratio, and asset turnover. Target: `eps_status` (1 = beat, 0 = miss).
