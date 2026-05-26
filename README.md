# earnings-indicator

Predict EPS beat/miss (`eps_status`) from quarterly financial features using PyTorch models.

## Prerequisites

Install these before cloning (macOS examples use [Homebrew](https://brew.sh/)):

| Tool | Purpose |
|------|---------|
| [Git](https://git-scm.com/) | Clone the repo |
| [Git LFS](https://git-lfs.com/) | Download `eps_estimate.csv` (~416 MB) |
| Python 3.12 | Virtualenv and dependencies |
| PostgreSQL 14+ | Full ETL pipeline only (not needed for notebooks-only setup) |

```bash
# macOS examples
brew install git git-lfs python@3.12 postgresql@18
git lfs install
```

On fresh macOS, `python3` may point to an older system Python — use `python3.12` explicitly if needed.

---

## Quick start (notebooks only)

Use this path if you only want to train/evaluate models. **No PostgreSQL or `.env` required** — processed CSVs are already in the repo.

```bash
git clone https://github.com/dhruvvd/earnings-indicator.git
cd earnings-indicator
git lfs pull   # required — without this, eps_estimate.csv is a stub pointer

python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

jupyter notebook
```

Open a notebook from the Jupyter file browser:

| Notebook | Data used |
|----------|-----------|
| `modelv1.ipynb` | `data/train.csv`, `data/val.csv`, `data/test.csv` |
| `modelv2.ipynb` | `data/findata.csv` |

Run all cells top to bottom. VS Code / Cursor also works if you select the `.venv` Python interpreter as the notebook kernel.

---

## Full pipeline setup

Use this path to reload raw Excel/CSV data into PostgreSQL and regenerate `data/findata.csv`.

### 1. Clone and Python environment

Same as quick start steps above, then:

```bash
cp .env.example .env
```

Edit `.env` with your PostgreSQL credentials:

```
DATABASE_URL=postgresql+psycopg2://your_user:your_password@localhost:5432/findata
```

### 2. PostgreSQL (macOS / Homebrew)

[`fdb.sql`](fdb.sql) creates tables and seeds ticker rows. [`fdb_features.sql`](fdb_features.sql) computes features **after** raw data is loaded.

```bash
brew services start postgresql@18
```

Add `psql` to your PATH if Homebrew prints instructions after install.

Create the database and an app user:

```bash
psql postgres
```

```sql
CREATE DATABASE findata;
CREATE USER your_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE findata TO your_user;
\c findata
GRANT ALL ON SCHEMA public TO your_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO your_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO your_user;
\q
```

Load the schema (run from the repo root):

```bash
psql -d findata -f fdb.sql
```

If `psql -d findata` fails, connect explicitly: `psql -h localhost -U $(whoami) -d findata`.

### 3. Run the pipeline

Order matters — feature SQL depends on data loaded by `scrape.py`:

```bash
source .venv/bin/activate   # if not already active

python scrape.py            # load Excel + CSV → PostgreSQL
psql -d findata -f fdb_features.sql   # compute features
python data_prep.py         # export → data/findata.csv
```

Then open `modelv1.ipynb` or `modelv2.ipynb` as in the quick start section.

```
stock_statements/  →  scrape.py  →  PostgreSQL (findata)
fdb.sql            →  tables + ticker seed
fdb_features.sql   →  feature engineering (after scrape)
data_prep.py       →  data/findata.csv
modelv1.ipynb      →  feedforward classifier (train/val/test splits)
modelv2.ipynb      →  LSTM sequence model
```

### Re-running the pipeline

`scrape.py` appends rows on each run. To reload from scratch:

```sql
-- in psql -d findata
TRUNCATE financial_statements, analyst_estimates RESTART IDENTITY CASCADE;
```

Then repeat step 3 (`scrape.py` → `fdb_features.sql` → `data_prep.py`). `fdb_features.sql` clears and rebuilds the `features` table automatically.

---

## Data

| Path | Description |
|------|-------------|
| `stock_statements/` | Raw Excel financial statements per ticker + EPS estimate/history CSVs |
| `data/findata.csv` | Joined feature matrix exported from PostgreSQL |
| `data/train.csv`, `val.csv`, `test.csv` | Train/validation/test splits for modelv1 |

`stock_statements/eps_estimate.csv` (~416 MB) is stored via Git LFS. Always run `git lfs pull` after cloning.

## Features

13 financial features per ticker/quarter: QoQ/YoY revenue and EPS growth, momentum, net/gross/operating margins, ROE, debt-to-equity, current ratio, cash ratio, and asset turnover. Target: `eps_status` (1 = beat, 0 = miss).

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `eps_estimate.csv` is tiny / scrape fails reading CSV | Run `git lfs install && git lfs pull` |
| `KeyError: 'DATABASE_URL'` | Copy `.env.example` to `.env` and set `DATABASE_URL` |
| FK violation on `companies` | Run `psql -d findata -f fdb.sql` before `scrape.py` |
| Empty `data/findata.csv` after export | Run `fdb_features.sql` **after** `scrape.py`, not before |
| Permission denied inserting rows | Grant schema/table permissions (see PostgreSQL step above) |
| `python` not found | Use `python3.12` instead |
