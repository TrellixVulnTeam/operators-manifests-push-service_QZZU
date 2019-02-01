# Operators Manifests Push Service (OMPS)
Service for pushing operators manifests to quay.io from various sources.

## Development

### Running Flask dev. server

To run app locally for testing, use:
```bash
FLASK_APP=omps/app.py flask run
```

### Installing with test dependencies

To install test dependencies from local directory use following:
```bash
pip install '.[test]'
```