# Development

To start developing, after cloning this repo (and preferably create a virtual environment), run the following command to
install all dependencies:

    pip install -U -e .

Install all required development packages:

    pip install -r requirements-dev.txt

To test the functioning of the package, run

    coverage run -m pytest

To understand the coverage of the test above, run

    coverage report

To check code style compliance, run

    flake8 .

For static security check, run

    bandit -r .

For type annotation test, run

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
