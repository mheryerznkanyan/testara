# Testara Documentation

This directory contains the source for Testara's documentation site, built with [MkDocs Material](https://squidfunk.github.io/mkdocs-material/).

## Local Development

### Install Dependencies

```bash
pip install -e ".[docs]"
```

### Serve Locally

```bash
mkdocs serve
```

Visit http://localhost:8000

### Build Static Site

```bash
mkdocs build
```

Output in `site/` directory.

## Deployment

Documentation is automatically deployed to GitHub Pages on push to `main`.

### Manual Deployment

```bash
mkdocs gh-deploy
```

## Structure

```
docs/
├── index.md                    # Homepage
├── getting-started/           # Installation & setup
│   ├── quickstart.md
│   ├── installation.md
│   └── configuration.md
├── usage/                     # How to use Testara
│   ├── generating-tests.md
│   ├── running-tests.md
│   └── rag-indexing.md
├── architecture/              # Technical deep dives
│   ├── overview.md
│   ├── rag.md
│   └── generation.md
├── advanced/                  # Advanced topics
│   ├── docker.md
│   ├── ci-cd.md
│   └── customization.md
├── api/                       # API reference
│   ├── rest.md
│   └── python.md
└── contributing/              # Contribution guides
    ├── guide.md
    └── development.md
```

## Writing Guide

### Code Blocks

Use syntax highlighting:

\`\`\`python
def hello():
    print("Hello, world!")
\`\`\`

### Admonitions

```markdown
!!! tip "Pro Tip"
    This is a helpful tip!

!!! warning "Caution"
    Be careful with this.

!!! bug "Known Issue"
    This is a known limitation.
```

### Diagrams

Use Mermaid for diagrams:

\`\`\`mermaid
graph LR
    A[Start] --> B[End]
\`\`\`

## Contributing

See [Contributing Guide](../CONTRIBUTING.md) for documentation contribution guidelines.
