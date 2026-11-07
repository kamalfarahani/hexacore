# AGENTS.md

Guidance for AI coding agents (and humans) working in this repository


## Docstrings Conventions

- Write docstrings in Google style, compatible with Sphinx's Napoleon extension.
- Use standard sections such as `Args`, `Attributes`, `Returns`, and `Raises` where applicable.
- Do not include type hints in docstrings. Keep type annotations in Python signatures and field declarations; document descriptions, constraints, and behavior in docstrings.
- When adding docstrings to the classes, don't repeat information that is already clear from the class signature or attributes. Focus on describing the purpose, behavior, and any important usage notes for the class.

## Testing Conventions

- Never use mocking or patching in tests, including `unittest.mock`, `patch`, or `monkeypatch`. Test real implementations and behavior.
- When a test needs a substitute object to perform an operation, use an instance of a fake implementation that follows the object's interface and provides the required behavior.