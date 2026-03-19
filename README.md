# AirForm

![PyPI version](https://img.shields.io/pypi/v/AirForm.svg)

Pydantic-native form validation and rendering. Define a model, get a validated, rendered HTML form. Works with or without Air web framework.

* GitHub: https://github.com/feldroy/AirForm/
* PyPI package: https://pypi.org/project/AirForm/
* Created by: **[Audrey M. Roy Greenfeld](https://audrey.feldroy.com/)** | GitHub https://github.com/audreyfeldroy | PyPI https://pypi.org/user/audreyr/
* Free software: MIT License

## Features

* TODO

## Documentation

Documentation is built with [Zensical](https://zensical.org/) and deployed to GitHub Pages.

* **Live site:** https://feldroy.github.io/AirForm/
* **Preview locally:** `just docs-serve` (serves at http://localhost:8000)
* **Build:** `just docs-build`

API documentation is auto-generated from docstrings using [mkdocstrings](https://mkdocstrings.github.io/).

Docs deploy automatically on push to `main` via GitHub Actions. To enable this, go to your repo's Settings > Pages and set the source to **GitHub Actions**.

## Development

To set up for local development:

```bash
# Clone your fork
git clone git@github.com:your_username/AirForm.git
cd AirForm

# Install in editable mode with live updates
uv tool install --editable .
```

This installs the CLI globally but with live updates - any changes you make to the source code are immediately available when you run `airform`.

Run tests:

```bash
uv run pytest
```

Run quality checks (format, lint, type check, test):

```bash
just qa
```

## Author

AirForm was created in 2026 by Audrey M. Roy Greenfeld.

Built with [Cookiecutter](https://github.com/cookiecutter/cookiecutter) and the [audreyfeldroy/cookiecutter-pypackage](https://github.com/audreyfeldroy/cookiecutter-pypackage) project template.
