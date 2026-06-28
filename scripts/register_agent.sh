#!/bin/bash
# Register agent and configure permissions

set -e

source .env 2>/dev/null || true

NODE_URL="${CASPER_NODE_URL:-https://rpc.testnet.casper.casperlabs.io}"
CHAIN_NAME="${CASPER_CHAIN_NAME:-casper-testnet}"
SECRET_KEY="${AGENT_SECRET_KEY:-./keys/agent.pem}"
PAYMENT="1000000000"

echo "=== Registering Agent ==="

# Register agent in AgentRegistry
echo "[1/2] Registering agent identity..."
casper-client put-deploy \
  --node-address "$NODE_URL" \
  --chain-name "$CHAIN_NAME" \
  --secret-key "$SECRET_KEY" \
  --session-hash "$REGISTRY_HASH" \
  --session-entry-point "register_agent" \
  --session-arg 'name:string="YieldOptimizer-v1"' \
  --session-arg 'strategy:string="Autonomous yield rebalancing across RWA-backed pools"' \
  --payment-amount "$PAYMENT"

# Authorize agent as oracle submitter
echo "[2/2] Authorizing agent as Oracle submitter..."
AGENT_ACCOUNT=$(casper-client account-address --secret-key "$SECRET_KEY" 2>/dev/null | tail -1)
casper-client put-deploy \
  --node-address "$NODE_URL" \
  --chain-name "$CHAIN_NAME" \
  --secret-key "$SECRET_KEY" \
  --session-hash "$ORACLE_HASH" \
  --session-entry-point "authorize_submitter" \
  --session-arg "agent:account_hash='$AGENT_ACCOUNT'" \
  --payment-amount "$PAYMENT"

# Authorize agent for rebalance
echo "[3/3] Authorizing agent for pool rebalance..."
casper-client put-deploy \
  --node-address "$NODE_URL" \
  --chain-name "$CHAIN_NAME" \
  --secret-key "$SECRET_KEY" \
  --session-hash "$YIELD_POOL_HASH" \
  --session-entry-point "authorize_agent" \
  --session-arg "agent:account_hash='$AGENT_ACCOUNT'" \
  --payment-amount "$PAYMENT"

echo ""
echo "=== Agent Registered and Authorized ==="
