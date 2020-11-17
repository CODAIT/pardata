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
