# real-estate-community-ranking-backend

A tool to rank communities in the Phoenix metro area based on a homebuyer's needs/wants.

## Architecture

![Real Estate Community Ranking Diagram](architecture/real-estate-community-ranking.svg)

The backend service consists of a REST API, several Lambda functions, and a simple state machine as detailed in the architecture diagram.

## Dependencies

### Python environment

Create a Python 3.9+ environment and install all the project dependencies.

```bash
pip install -r service/lambdas/requirements.txt
```
