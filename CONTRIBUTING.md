# Development

## Quick Setup

To start developing, after cloning this repo (and preferably create a virtual environment), run the following command to
install all dependencies:

    pip install -U -e .

Install all required development packages:

    pip install -r requirements-dev.txt

To run all tests on all available Python versions configured to work with PyDAX, run:

    tox

By default `tox` uses `virtualenv` for creating each test environment (such as for each Python version). If you would prefer `tox` to use `conda`, run:

    pip install tox-conda

## Running Tox Tests Individually

To test the functioning of the package, run:

    coverage run -m pytest

To understand the coverage of the test above, run:

    coverage report

To check Python code style compliance, run:

    flake8 .

To check YAML code style compliance, run:

    yamllint -c .yamllint.yaml .

For static security check, run:

    bandit -r .

For type annotation test, run:

    mypy pydax

## Where to Expose a Symbol (Function, Class, etc.)?

Generally speaking:

- If a symbol is likely used by a casual user regularly, it should be exposed in `pydax/__init__.py`. This gives casual
  users the cleanest and the most direct access.
- If a symbol is used only by a power user, but is unlikely used by a casual user regularly, it should be exposed in a
  file that does not start with an underscore, such as `pydax/schema.py`; or in the `__init__.py` file in a subdirectory
  that does not start with an underscore, such as `pydax/loaders/__init__.py`. The rationale is that the amount of such
  symbols is usually large and if we expose them at the root level of the package, it would be messy and likely confuse
  casual users.
- If a symbol is solely used for internal purpose, it should be exposed only in files starting with a single underscore,
  such as `pydax/_dataset.py`.

Please keep in mind that the criteria above are not meant to be rigid: They should be applied flexibly in light of
factors such as where existing symbols are placed and other potentially important considerations (if any).

## Where to Import a Symbol?

When referencing a symbol that is exposed to a user, in general, we prefer importing the symbol from where the package
publicly exposes it over importing from where the source code of the symbol is defined, e.g., use `from .schema import
SchemaDict` rather than `from ._schema import SchemaDict`. This way we have more code paths that would go through what
the user would actually experience and hopefully would give us more chances to discover bugs.
