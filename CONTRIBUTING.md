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
