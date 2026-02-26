# Triangular Arbitrage Scanner (Trader Edition)

This project is not a "magic AI bot". It is a deterministic cycle scanner with a conscious decision layer.

Goal: only surface setups that still look positive after realistic trading costs.

## What Changed

The codebase now includes a `TradingLogicDirector` in `triangular_arbitrage/director.py`.

It separates two responsibilities:

1. **Detection** (`triangular_arbitrage/detector.py`)  
   Finds the best currency cycle by gross multiplier.
2. **Decision** (`triangular_arbitrage/director.py`)  
   Applies taker fees, slippage assumptions, and a minimum net edge threshold before signaling `TRADE`.

This prevents "looks good on paper" cycles from being treated as executable opportunities.

## Experimental Trading Logic

The director evaluates:

- `gross_profit_multiplier` from the detector
- cost model per leg: `taker_fee_bps + slippage_bps`
- compounded net multiplier across all legs
- execution gate: `min_net_profit_bps`

Decision rule:

`TRADE` only if expected net edge (in bps) is above threshold.  
Otherwise: `SKIP` with an explicit reason.

## Why Traders Care

Most public arbitrage demos fail because they:

- ignore fees
- ignore slippage
- report stale opportunities
- trigger on tiny edges that disappear on fill

This implementation explicitly addresses the first three at the decision layer and is parameterized for stricter filters.

## Quick Start

### Requirements

- Python 3.10+

### Install

```bash
pip install -r requirements.txt
```

### Run

```bash
python main.py
```

## Example Output

```text
Scanning...
-------------------------------------------
Best gross cycle on bitget: 0.32710%
Expected net edge after costs: 0.17180%
Decision: TRADE (Net edge clears threshold.)
1. buy BTC with USDT at 0.00003
2. sell BTC for ETH at 14.88123
3. sell ETH for USDT at 2060.20000
-------------------------------------------
```

If the net edge is below threshold:

```text
Decision: SKIP (Net edge below threshold after costs (9.20 bps < 15.00 bps).)
```

## Strategy Parameters

Edit `main.py` and tune `DirectorConfig`:

- `exchange_name`: ccxt exchange id (example: `bitget`, `binanceus`)
- `max_cycle`: set `3` for triangular cycles
- `taker_fee_bps`: fee assumption per leg
- `slippage_bps`: slippage assumption per leg
- `min_net_profit_bps`: minimum net edge required to trade

## Experimental Analysis Template

Use this table while paper trading to validate profitability discipline:

| Date | Exchange | Gross Edge (bps) | Net Edge Model (bps) | Realized (bps) | Decision | Notes |
|---|---|---:|---:|---:|---|---|
| 2026-02-20 | bitget | 41.0 | 19.6 | 14.2 | TRADE | Partial fill on leg 2 |
| 2026-02-21 | bitget | 24.0 | 8.5 | - | SKIP | Correct skip, edge too thin |
| 2026-02-22 | bitget | 55.0 | 33.1 | 29.4 | TRADE | Clean execution |

Interpretation:

- positive realized bps on trades and avoided thin edges indicate the director logic is working
- if realized bps consistently trails model, increase slippage and threshold

## Profitability Statement

This bot is designed to be profitable **only when your market + fee regime supports positive net edge after costs**.

It is not guaranteed profit. Treat it as an execution filter that enforces trading discipline, then validate with paper logs and live micro-size before scaling.
