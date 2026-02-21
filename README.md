# poly-auto-claim

Auto-redeems won Polymarket positions every 5 minutes (configurable).

## Setup

1. Copy `.env.example` to `.env` and fill in your credentials:
   ```
   PRIVATE_KEY=0x...      # your 64-char hex private key
   WALLET_ADDRESS=0x...   # your EIP-55 checksummed wallet address
   ```

2. Build and run:
   ```bash
   docker build -t poly-auto-claim .
   docker run --env-file .env poly-auto-claim
   ```

## Configuration

| Variable | Required | Default | Description |
|---|---|---|---|
| `PRIVATE_KEY` | yes | — | 0x-prefixed hex private key (66 chars) |
| `WALLET_ADDRESS` | yes | — | EIP-55 checksummed wallet address |
| `POLYGON_RPC_URL` | no | `https://polygon-rpc.com` | Polygon RPC endpoint (use a dedicated provider for production) |
| `POLL_INTERVAL` | no | `300` | Seconds between redemption polls |

## How it works

1. Every `POLL_INTERVAL` seconds, fetches your positions from the Polymarket data API
2. Filters for positions where `redeemable=true` and `size > 0`
3. For each redeemable position, submits a `redeemPositions` transaction on Polygon
4. Handles both standard CTF markets and NegRisk markets automatically

## Running tests

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

## Stopping

Send `SIGINT` (Ctrl+C) or `SIGTERM` — the bot finishes the current cycle and exits cleanly.
