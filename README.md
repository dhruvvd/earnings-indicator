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
| [PostgreSQL extension](https://marketplace.visualstudio.com/items?itemName=ckolkman.vsc-postgresql) | Run SQL in Cursor/VS Code (full pipeline only; replaces terminal `psql`) |

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
git lfs install
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

Same as quick start steps above, then copy the env template (you'll fill in `DATABASE_URL` in step 2):

```bash
cp .env.example .env
```

### 2. PostgreSQL (macOS / Homebrew + Cursor/VS Code)

[`fdb.sql`](fdb.sql) creates tables and seeds ticker rows. [`fdb_features.sql`](fdb_features.sql) computes features **after** raw data is loaded.

Start the database server:

```bash
brew services start postgresql@18
```

Install the **PostgreSQL** extension in Cursor or VS Code ([marketplace link](https://marketplace.visualstudio.com/items?itemName=ckolkman.vsc-postgresql)). All SQL below is run through the extension — no terminal `psql` required.

#### Connect in Cursor/VS Code

1. Open the Command Palette (`Cmd+Shift+P`) → **PostgreSQL: Add Connection**
2. Use your macOS username (output of `whoami`), host `localhost`, port `5432`, database `postgres` (the default admin DB)
3. Leave password blank for typical local Homebrew installs

#### Create the database

Open a new SQL editor (Command Palette → **PostgreSQL: New Query**), connect to `postgres`, and run:

**Option A — use your macOS user (simplest):**

```sql
CREATE DATABASE findata;
```

Set `.env` to match (replace `YOUR_MACOS_USERNAME` with `whoami`):

```
DATABASE_URL=postgresql+psycopg2://YOUR_MACOS_USERNAME@localhost:5432/findata
```

**Option B — dedicated app user:**

```sql
CREATE DATABASE findata;
CREATE USER your_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE findata TO your_user;
```

Then add a second connection in the extension pointing at database `findata`, open a new query, and run:

```sql
GRANT ALL ON SCHEMA public TO your_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO your_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO your_user;
```

Set `.env` to:

```
DATABASE_URL=postgresql+psycopg2://your_user:your_password@localhost:5432/findata
```

#### Load the schema

1. Switch your extension connection to the `findata` database (or add a `findata` connection)
2. Open [`fdb.sql`](fdb.sql) in the editor
3. Run the entire file (select all → **PostgreSQL: Execute Query**, or use the extension's run command on the active file)

You will run [`fdb_features.sql`](fdb_features.sql) the same way in step 3, after `scrape.py`.

<details>
<summary>Terminal alternative (<code>psql</code>)</summary>

```bash
psql postgres -c "CREATE DATABASE findata;"
psql -d findata -f fdb.sql
# after scrape.py:
psql -d findata -f fdb_features.sql
```

</details>

### 3. Run the pipeline

Order matters — feature SQL depends on data loaded by `scrape.py`:

```bash
source .venv/bin/activate   # if not already active

python3.12 scrape.py            # load Excel + CSV → PostgreSQL
```

After `scrape.py` finishes, open [`fdb_features.sql`](fdb_features.sql) in Cursor/VS Code and run the entire file through the PostgreSQL extension (connected to `findata`). Then export:

```bash
python3.12 data_prep.py         # export → data/findata.csv
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

`scrape.py` appends rows on each run. To reload from scratch, run this in a PostgreSQL extension query (connected to `findata`):

```sql
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
| FK violation on `companies` | Run [`fdb.sql`](fdb.sql) through the PostgreSQL extension before `scrape.py` |
| Empty `data/findata.csv` after export | Run [`fdb_features.sql`](fdb_features.sql) **after** `scrape.py`, not before |
| Permission denied inserting rows | Grant schema/table permissions (see PostgreSQL step above) |
| Extension can't connect | Confirm `brew services start postgresql@18` and use your macOS username with a blank password |
| `python` not found | Use `python3.12` instead |
