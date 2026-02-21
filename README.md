# poly-auto-claim

Automatically claims won Polymarket positions every 5 minutes.

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- Your Polymarket wallet private key and address

## Setup

**1. Clone the repo**
```bash
git clone https://github.com/Tonyyeahx/polymarket-auto-claim.git
cd polymarket-auto-claim
```

**2. Create your `.env` file**
```bash
cp .env.example .env
```

Open `.env` and fill in your credentials:
```
PRIVATE_KEY=0x...      # your wallet private key (64 hex chars after 0x)
WALLET_ADDRESS=0x...   # your wallet address (42 chars)
```

**3. Start the bot**
```bash
docker compose up -d
```

The bot is now running in the background. It will keep running even if you close the terminal or restart your machine.

## Useful commands

```bash
# Watch live logs
docker compose logs -f

# Stop the bot
docker compose down

# Restart the bot
docker compose restart
```

## Configuration

| Variable | Required | Default | Description |
|---|---|---|---|
| `PRIVATE_KEY` | yes | — | 0x-prefixed hex private key |
| `WALLET_ADDRESS` | yes | — | Wallet address |
| `POLYGON_RPC_URL` | no | `https://polygon-rpc.com` | Polygon RPC endpoint |
| `POLL_INTERVAL` | no | `120` | Seconds between checks |

## How it works

Every `POLL_INTERVAL` seconds the bot checks your Polymarket positions for any that are won and unclaimed, then submits an on-chain `redeemPositions` transaction on Polygon to collect them. Handles both standard and NegRisk markets automatically.
