# Python API Reference

Use Testara programmatically from Python.

*Documentation coming soon.*

## Example

```python
from rag.service import RAGService
from app.services.test_generator import TestGenerator

# Initialize services
rag = RAGService()
generator = TestGenerator()

# Generate test
test_code = generator.generate("test login flow")
```
