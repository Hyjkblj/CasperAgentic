.PHONY: all contracts agent-install agent-run frontend-dev deploy up down

# ─── Contracts ───

contracts:
	cd contracts && cargo build --target wasm32-unknown-unknown --release

contracts-check:
	cd contracts && cargo check

# ─── Agent ───

agent-install:
	cd agent && pip install -r requirements.txt

agent-run:
	cd agent && python main.py

# ─── Mock x402 Server ───

mock-install:
	cd mock_x402_server && pip install -r requirements.txt

mock-run:
	cd mock_x402_server && python main.py

# ─── Frontend ───

frontend-install:
	cd frontend && npm install

frontend-dev:
	cd frontend && npm run dev

frontend-build:
	cd frontend && npm run build

# ─── Docker ───

up:
	docker-compose up -d

down:
	docker-compose down

# ─── All ───

install: agent-install mock-install frontend-install

dev:
	@echo "Starting mock x402 server..."
	cd mock_x402_server && python main.py &
	@echo "Starting agent..."
	cd agent && python main.py &
	@echo "Starting frontend..."
	cd frontend && npm run dev

all: contracts frontend-build
