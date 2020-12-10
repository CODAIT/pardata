# Development

## Quick Setup

### Use `tox`

To start developing, the recommended way is to use `tox`. This way, your development environment is automatically
prepared by `tox`, including virtual environment setup, dependency management, installing `pydax` in development mode.

1. Install `tox`:

    $ pip install -U -r requirements/tox.txt  # If you are inside a virtual environment, conda environment
    $ pip3 install --user -U tox  # If you are outside any virtual environment or conda environment and don't have tox installed

2. At the root directory of `pydax`, run:

    $ tox -e dev

   To force updating development environment in the future, run `tox --recreate -e dev` when the development environment
   is not activated.

3. To activate the development environment, run:

    $ . .tox/dev/bin/activate

### Traditional Method

Alternatively, after cloning this repository (and preferably having created and activated a virtual environment), run
the following command to install all dependencies:

    $ pip install -U -e .

Install all required development packages:

    $ pip install -U -r requirements-dev.txt

## Run Tests

### Run All Tests

Before and after one stage of development, you may want to try whether the code would pass all tests.

To run all tests on the Python versions that are supported by PyDAX and available on your system, run:

    $ tox -s

When you are brave, to force running all tests on all Python versions that are supported by PyDAX, run:

    $ tox

By default `tox` uses `virtualenv` for creating each test environment (such as for each Python version). If you would
prefer `tox` to use `conda`, run:

    $ pip install tox-conda

### Running Part of the Tests

During development, you likely would like to run only part of the tests to save time.

To run all static tests, run:

    $ tox -e lint

To run all runtime tests on the Python version in the development environment, run:

    $ tox -e py

To run only a specific runtime test, run:

    $ pytest -vk [test_name]  # e.g., pytest -vk test_default_data_dir

Read [pytest command line document](https://docs.pytest.org/en/stable/usage.html) for its more advanced usage.

To run document generation tests, run:

    $ tox -e docs

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

## Continuous Integration (CI)

We prefer keeping CI configuration files, namely `.travis.yml` and `.appveyor.yml` simple and unscrambled. Normally,
only test environment, such as Python version, OS and tox environmental variables, or anything that is specific to the
CI system, such as failure notification. Complicated test dependencies and other test dealings should go to `tox.ini`
and their respective test files in `tests/`.

## Docs

The easiest way to generate the docs is to run the `tox` docs test environment. The html index file generates at `.tox/docs_out/index.html`:

    tox -e docs

To run docs tests individually or to generate the docs, cd into the `docs/` directory and run any of the commands below:

    cd docs

To generate the stub files for the API Reference section (these are used by the `autosummary` toctree option):

    sphinx-autogen -o source/api_reference/autosummary source/api_reference/*.rst

To generate the HTML files for the docs to the `build` directory (note: this will automatically regenerate the stubfiles used by `autosummary` prior to generating the html files):

    sphinx-build -d build/doctrees source build/html -b html

To check reST code style compliance, run:

    rstcheck -r docs/source/miscellaneous docs/source/user_guide docs/source/api_reference/*.rst

The reST code style compliance is also checked by the `tox` lint test environment if you prefer to use that:

    tox -e lint

## Dependency Version Pinning Policy

We should pin the versions of all Python packages that we are using solely for testing and doc
generating for a stable test and doc env (e.g., future incompatibility, regression, etc.). We want
to pin these because, in this project, we use these packages solely for deployment of our development
environment (i.e., running tests and generating docs) and we want stable packages that are used by
us for these purposes. We let GitHub's Dependabot verify that bumping the versions won't
break anything before we actually upgrade any of these dependencies.

We should not pin the actual dependencies of PyDAX (as specified in `setup.py`), because PyDAX is an
intermediate software layer -- those should be pinned only by the actual deployed application that
depends on PyDAX. We should only code the info of supported versions of these dependencies. If there
is some regression or incompatibilities in the latest versions of our dependencies, we should either
work around them, or update `setup.py` to avoid depending on those versions.
