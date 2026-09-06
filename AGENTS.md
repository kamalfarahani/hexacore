Write Google-style docstrings compatible with Sphinx's Napoleon extension.
Keep type information in Python annotations, not in docstrings. In `Args`,
write `name: Description.` without a type. In `Returns` and `Yields`, describe
the value without a type prefix. For properties and attributes, describe their
meaning without repeating their annotations. Use `Raises` to name exceptions
and explain when they occur; exception names are allowed in this section.
Include only sections relevant to the documented object.
