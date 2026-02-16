# Only check style
check:
	ruff check src/

# Format
format:
	ruff format src/ && isort src/ && ruff check --fix

dev-check:
	@grep -q "dev=True" src/shared.py && (echo "❌ dev=True found!" && exit 1) || echo "✅ OK"