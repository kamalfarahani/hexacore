# hexacore

A hexagonal architecture framework for Python.

## Documentation

The documentation is built with [Sphinx](https://www.sphinx-doc.org/) and
lives under `docs/`. To build it locally:

```bash
uv sync --group docs
uv run --group docs sphinx-build -b html docs/source docs/_build/html
```

Then open `docs/_build/html/index.html` in a browser.
