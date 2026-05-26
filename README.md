# earnings-indicator

Predict EPS beat/miss (`eps_status`) from quarterly financial features using PyTorch models.

## Prerequisites

- Python 3.12
- PostgreSQL
- [Git LFS](https://git-lfs.com/) (required for the large raw data file)

## Setup

```bash
git clone <repo-url>
cd earnings-indicator
git lfs install
git lfs pull

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env with your PostgreSQL connection string
```

Create a PostgreSQL database named `findata`, then apply the schema:

```bash
psql -d findata -f fdb.sql
```

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
