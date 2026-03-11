# Contributing to Testara

Thank you for your interest in contributing! 🎉

## Ways to Contribute

- 🐛 Report bugs
- 💡 Suggest features
- 📝 Improve documentation
- 🔧 Submit pull requests

---

## Bug Reports

**Before submitting:**
- Search existing issues
- Check if it's already fixed in `main`

**Include:**
- Testara version
- macOS version
- Xcode version
- Steps to reproduce
- Expected vs actual behavior
- Error messages / logs

---

## Feature Requests

**Before submitting:**
- Check if it already exists
- Consider if it fits the project scope

**Include:**
- Use case / problem you're solving
- Proposed solution
- Alternative solutions considered

---

## Pull Requests

### Setup

```bash
# Fork the repo
git clone https://github.com/YOUR_USERNAME/testara
cd testara

# Create feature branch
git checkout -b feature/your-feature-name

# Make changes
# ...

# Test your changes
./run_validation.sh

# Commit
git commit -m "Add feature: your feature"

# Push
git push origin feature/your-feature-name
```

### Guidelines

**Code:**
- Follow PEP 8 (Python)
- Add tests for new features
- Update documentation
- Keep commits focused and atomic

**Commits:**
- Use clear, descriptive messages
- Format: `type: description` (e.g., `fix: correct navigation extraction`)
- Types: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`

**Tests:**
- Add tests for new features
- Ensure existing tests pass
- Run: `pytest tests/`

**Documentation:**
- Update README if needed
- Add docstrings to new functions
- Update relevant guides

---

## Development Setup

```bash
# Install dependencies
pip install -r backend/requirements.txt

# Run tests
pytest tests/

# Run linter
flake8 backend/

# Start dev server
cd backend
uvicorn app.main:app --reload --port 8000
```

---

## Code Review Process

1. Submit PR
2. Automated checks run (CI)
3. Maintainer reviews
4. Address feedback
5. Merge!

**Review criteria:**
- ✅ Tests pass
- ✅ Code quality
- ✅ Documentation updated
- ✅ No breaking changes (or justified)

---

## Questions?

- Open a [Discussion](https://github.com/mheryerznkanyan/testara/discussions)
- Ask in [Issues](https://github.com/mheryerznkanyan/testara/issues)

---

## License

By contributing, you agree your contributions will be licensed under the MIT License.

---

Thank you for making Testara better! 🚀
