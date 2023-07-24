# real-estate-community-ranking-backend

A tool to rank communities in the Phoenix metro area based on a homebuyer's needs/wants.

## Architecture

![Real Estate Community Ranking Diagram](architecture/real-estate-community-ranking.svg)

The backend service consists of a REST API, several Lambda functions, and a simple state machine as detailed in the architecture diagram.

## Dependencies

### Python environment

Create a Python 3.9+ environment and install all the project dependencies.

```bash
# service deps
pip install -r service/lambdas/requirements.txt
```

```bash
# testing deps
pip install -r tests/requirements.txt
```

## Usage

Important❗: All scripts are designed to be executed from the project root directory (folder containing *this* README).

### tests

This project employs `pytest` for unit testing. After developing new functionality, add new test(s). Create a new function in an existing test script or create a new test script entirely if a new function was created. For test function names, follow the format: `test_<lambda_function>`.

The following commands are commonly used for testing this project.

```bash
# runs all tests observed by pytest
pytest -v
```

```bash
# runs tests only in the specified test script
pytest -v tests/test_rank_communities.py
```

You can also report test coverage:

```bash
# runs all test scripts
pytest -v --cov --cov-report html
```
