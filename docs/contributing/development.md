# Development Setup

Set up Testara for development.

## Prerequisites

- macOS with Xcode
- Python 3.11+
- Node.js 20+

## Setup

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/testara
cd testara

# Create feature branch
git checkout -b feature/my-feature

# Install dependencies
pip install -e ".[docs]"
cd frontend && npm install && cd ..

# Run tests
pytest tests/

# Start development servers
./start.sh
```

## Project Structure

```
testara/
├── backend/          # FastAPI backend
├── frontend/         # Next.js frontend
├── rag/             # RAG pipeline
├── docs/            # Documentation
└── tests/           # Test suite
```

## Testing

```bash
# Run all tests
pytest tests/

# Run specific test
pytest tests/test_generator.py

# With coverage
pytest --cov=backend tests/
```

## Documentation

Build docs locally:

```bash
pip install -e ".[docs]"
mkdocs serve
```

Visit http://localhost:8000

For more details, see [CONTRIBUTING.md](https://github.com/mheryerznkanyan/testara/blob/main/CONTRIBUTING.md).
