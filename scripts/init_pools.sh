#!/bin/bash
# Initialize yield pools and configure permissions

set -e

source .env 2>/dev/null || true

NODE_URL="${CASPER_NODE_URL:-https://rpc.testnet.casper.casperlabs.io}"
CHAIN_NAME="${CASPER_CHAIN_NAME:-casper-testnet}"
SECRET_KEY="${AGENT_SECRET_KEY:-./keys/agent.pem}"
PAYMENT="1000000000"

echo "=== Initializing Yield Pools ==="

# Create pools
echo "[1/3] Creating Stable Pool (3% APY)..."
casper-client put-deploy \
  --node-address "$NODE_URL" \
  --chain-name "$CHAIN_NAME" \
  --secret-key "$SECRET_KEY" \
  --session-hash "$YIELD_POOL_HASH" \
  --session-entry-point "create_pool" \
  --session-arg "apy_basis_points:u64='300'" \
  --payment-amount "$PAYMENT"

echo "[2/3] Creating Growth Pool (6% APY)..."
casper-client put-deploy \
  --node-address "$NODE_URL" \
  --chain-name "$CHAIN_NAME" \
  --secret-key "$SECRET_KEY" \
  --session-hash "$YIELD_POOL_HASH" \
  --session-entry-point "create_pool" \
  --session-arg "apy_basis_points:u64='600'" \
  --payment-amount "$PAYMENT"

echo "[3/3] Creating High Yield Pool (9% APY)..."
casper-client put-deploy \
  --node-address "$NODE_URL" \
  --chain-name "$CHAIN_NAME" \
  --secret-key "$SECRET_KEY" \
  --session-hash "$YIELD_POOL_HASH" \
  --session-entry-point "create_pool" \
  --session-arg "apy_basis_points:u64='900'" \
  --payment-amount "$PAYMENT"

echo ""
echo "=== Pools Initialized ==="
