#!/usr/bin/env python3
"""
Contract deployment helper.

This script deploys compiled WASM contracts to Casper testnet.
Requires: casper-client CLI installed and agent key in ./keys/agent.pem

Usage:
    python scripts/deploy_contracts.py
"""

import subprocess
import sys
import os
import json

NODE_URL = os.getenv("CASPER_NODE_URL", "https://rpc.testnet.casper.casperlabs.io")
CHAIN_NAME = os.getenv("CASPER_CHAIN_NAME", "casper-testnet")
SECRET_KEY = os.getenv("AGENT_SECRET_KEY", "./keys/agent.pem")
PAYMENT = os.getenv("PAYMENT_AMOUNT", "5000000000")

CONTRACTS = [
    ("agent_registry", "AgentRegistry"),
    ("rwa_oracle", "RwaOracle"),
    ("yield_pool", "YieldPool"),
]


def run_casper_client(args: list[str]) -> str:
    """Run casper-client with common flags."""
    cmd = [
        "casper-client",
        "--node-address", NODE_URL,
        "--chain-name", CHAIN_NAME,
        "--secret-key", SECRET_KEY,
    ] + args
    print(f"  Running: {' '.join(cmd[:6])}...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  Error: {result.stderr}")
        sys.exit(1)
    return result.stdout


def deploy_contract(wasm_name: str, label: str) -> str:
    """Deploy a single contract and return the deploy hash."""
    wasm_path = f"contracts/target/wasm32-unknown-unknown/release/{wasm_name}.wasm"
    if not os.path.exists(wasm_path):
        print(f"  Error: {wasm_path} not found. Run 'cargo build --target wasm32-unknown-unknown --release' first.")
        sys.exit(1)

    output = run_casper_client([
        "put-deploy",
        "--session-path", wasm_path,
        "--payment-amount", PAYMENT,
    ])

    try:
        data = json.loads(output)
        return data.get("deploy_hash", "unknown")
    except json.JSONDecodeError:
        return output.strip()


def main():
    print("=" * 50)
    print("Deploying YieldAgent Contracts to Casper Testnet")
    print("=" * 50)
    print(f"Node: {NODE_URL}")
    print(f"Chain: {CHAIN_NAME}")
    print(f"Key: {SECRET_KEY}")
    print()

    # Check prerequisites
    if not os.path.exists(SECRET_KEY):
        print(f"Error: Key file not found: {SECRET_KEY}")
        print("Run: casper-client keygen ./keys")
        sys.exit(1)

    # Check casper-client is installed
    try:
        subprocess.run(["casper-client", "--version"], capture_output=True, check=True)
    except FileNotFoundError:
        print("Error: casper-client not found in PATH")
        print("Install: cargo install casper-client")
        print("Or download from: https://github.com/casper-ecosystem/casper-client-rs/releases")
        sys.exit(1)

    results = {}
    for wasm_name, label in CONTRACTS:
        print(f"[{label}] Deploying {wasm_name}...")
        deploy_hash = deploy_contract(wasm_name, label)
        results[label] = deploy_hash
        print(f"  Deploy hash: {deploy_hash}")
        print()

    print("=" * 50)
    print("Deployment Complete!")
    print("=" * 50)
    print()
    print("Add these to your .env file:")
    for label, hash_val in results.items():
        key = f"{label.upper()}_HASH"
        print(f"  {key}={hash_val}")
    print()
    print("Note: Contract hashes will be available after deploy confirmation (~30s)")
    print("Check status: casper-client get-deploy --node-address {NODE_URL} <deploy_hash>")


if __name__ == "__main__":
    main()
