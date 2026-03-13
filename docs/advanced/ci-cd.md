# CI/CD Integration

Integrate Testara with your continuous integration pipeline.

*Documentation coming soon.*

## GitHub Actions Example

```yaml
- name: Generate and run tests
  run: |
    python -m rag.cli ingest --app-dir ./ios-app
    curl -X POST http://localhost:8000/generate-test-with-rag \
      -d '{"description": "test critical user flows"}'
```
