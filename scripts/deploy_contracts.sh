#!/bin/bash
# Deploy all contracts to Casper testnet

set -e

NODE_URL="${CASPER_NODE_URL:-https://rpc.testnet.casper.casperlabs.io}"
CHAIN_NAME="${CASPER_CHAIN_NAME:-casper-testnet}"
SECRET_KEY="${AGENT_SECRET_KEY:-./keys/agent.pem}"
PAYMENT="${PAYMENT_AMOUNT:-5000000000}"

echo "=== Deploying YieldAgent Contracts ==="
echo "Node: $NODE_URL"
echo "Chain: $CHAIN_NAME"
echo "Key: $SECRET_KEY"
echo ""

# Build contracts
echo "[1/4] Building contracts..."
cd contracts
cargo build --target wasm32-unknown-unknown --release
cd ..

# Deploy AgentRegistry
echo "[2/4] Deploying AgentRegistry..."
REGISTRY_DEPLOY=$(casper-client put-deploy \
  --node-address "$NODE_URL" \
  --chain-name "$CHAIN_NAME" \
  --secret-key "$SECRET_KEY" \
  --session-path contracts/target/wasm32-unknown-unknown/release/agent_registry.wasm \
  --payment-amount "$PAYMENT" 2>&1)
REGISTRY_HASH=$(echo "$REGISTRY_DEPLOY" | grep -o '"deploy_hash":"[^"]*"' | cut -d'"' -f4)
echo "  Deploy hash: $REGISTRY_HASH"

# Deploy RwaOracle
echo "[3/4] Deploying RwaOracle..."
ORACLE_DEPLOY=$(casper-client put-deploy \
  --node-address "$NODE_URL" \
  --chain-name "$CHAIN_NAME" \
  --secret-key "$SECRET_KEY" \
  --session-path contracts/target/wasm32-unknown-unknown/release/rwa_oracle.wasm \
  --payment-amount "$PAYMENT" 2>&1)
ORACLE_HASH=$(echo "$ORACLE_DEPLOY" | grep -o '"deploy_hash":"[^"]*"' | cut -d'"' -f4)
echo "  Deploy hash: $ORACLE_HASH"

# Deploy YieldPool
echo "[4/4] Deploying YieldPool..."
POOL_DEPLOY=$(casper-client put-deploy \
  --node-address "$NODE_URL" \
  --chain-name "$CHAIN_NAME" \
  --secret-key "$SECRET_KEY" \
  --session-path contracts/target/wasm32-unknown-unknown/release/yield_pool.wasm \
  --payment-amount "$PAYMENT" 2>&1)
POOL_HASH=$(echo "$POOL_DEPLOY" | grep -o '"deploy_hash":"[^"]*"' | cut -d'"' -f4)
echo "  Deploy hash: $POOL_HASH"

echo ""
echo "=== Deployment Complete ==="
echo "Add these to your .env file:"
echo "  REGISTRY_HASH=$REGISTRY_HASH"
echo "  ORACLE_HASH=$ORACLE_HASH"
echo "  YIELD_POOL_HASH=$POOL_HASH"
