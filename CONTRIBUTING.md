# Contributing to TeleOps

Thank you for your interest in contributing to TeleOps! This document provides guidelines for development and contribution.

## Development Setup

```bash
# Clone repository
git clone https://github.com/udaytamma/teleops.git
cd teleops

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install with development dependencies
pip install -e ".[dev]"

# Configure environment
cp .env.example .env
# Edit .env with your GEMINI_API_KEY
```

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=teleops --cov-report=term

# Run specific test file
pytest tests/test_api.py -v
```

## Code Style

We use `ruff` for linting and formatting:

```bash
# Check linting
ruff check teleops/ tests/

# Auto-fix issues
ruff check teleops/ tests/ --fix

# Format code
ruff format teleops/ tests/
```

## Project Structure

```
teleops/
├── teleops/           # Main package
│   ├── api/           # FastAPI endpoints
│   ├── data_gen/      # Synthetic data generation
│   ├── incident_corr/ # Alert correlation
│   ├── llm/           # LLM adapters and RCA
│   └── rag/           # RAG pipeline
├── ui/                # Streamlit dashboard
├── docs/              # Documentation and RAG corpus
├── tests/             # Test suite
└── storage/           # Persistent data
```

## Adding New Scenarios

1. Add scenario definition in `teleops/data_gen/generator.py`
2. Add baseline RCA rule in `teleops/llm/rca.py`
3. Add runbook to `docs/rag_corpus/` for RAG context
4. Add test case in `tests/`
5. Update scenario catalog in `docs/scenario_catalog.md`

## Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Make your changes
4. Run tests and linting
5. Commit with descriptive message
6. Push and open a Pull Request

## Questions?

Open an issue on GitHub or contact the maintainer.
