# AirForm

![PyPI version](https://img.shields.io/pypi/v/AirForm.svg)

Pydantic-native form validation and rendering. Define a model, get a validated, rendered HTML form. Built for [Air](https://github.com/feldroy/air), also works standalone with FastAPI, Starlette, Litestar, or any ASGI framework.

* GitHub: https://github.com/feldroy/AirForm/
* PyPI package: https://pypi.org/project/AirForm/
* Created by: **[Audrey M. Roy Greenfeld](https://audrey.feldroy.com/)** | GitHub https://github.com/audreyfeldroy | PyPI https://pypi.org/user/audreyr/
* Free software: MIT License

## Features

* Type-safe validated data via `AirForm[MyModel]` generic parameter
* Reads the full [AirField](https://github.com/feldroy/AirField) metadata vocabulary: Widget, Label, Placeholder, HelpText, Choices, Autofocus, PrimaryKey, Hidden, ReadOnly
* Auto-skips PrimaryKey and Hidden("form") fields in rendered output
* HTML5 validation attributes from Pydantic constraints (minlength, maxlength, required)
* Accessible by default: aria-invalid, aria-describedby, role="alert" on errors
* Textarea, select, and checkbox rendering from type annotations and metadata
* Swappable widget for custom renderers
* `from_request()` for async ASGI request handling (works with FastAPI Depends)

## Quick start

### With Air

```python
from air import AirForm, AirModel, AirField
import air

app = air.Air()

class Contact(AirModel):
    name: str
    email: str = AirField(type="email", label="Email Address")

class ContactForm(AirForm[Contact]):
    pass

@app.post("/contact")
async def submit(request: air.Request):
    form = await ContactForm.from_request(request)
    if form.is_valid:
        return air.Html(air.H1(f"Thanks, {form.data.name}!"))
    return air.Html(air.Raw(form.render()))
```

### Standalone (any ASGI framework)

```python
from pydantic import BaseModel
from airform import AirForm

class ContactModel(BaseModel):
    name: str
    email: str

class ContactForm(AirForm[ContactModel]):
    pass

# Validate
form = ContactForm()
form.validate({"name": "Audrey", "email": "audreyfeldroy@example.com"})
if form.is_valid:
    print(form.data.name)  # type-safe: editor knows this is str

# Render
html = ContactForm().render()
```

## Documentation

Documentation is built with [Zensical](https://zensical.org/) and deployed to GitHub Pages.

* **Live site:** https://feldroy.github.io/AirForm/
* **Preview locally:** `just docs-serve` (serves at http://localhost:8000)
* **Build:** `just docs-build`

API documentation is auto-generated from docstrings using [mkdocstrings](https://mkdocstrings.github.io/).

Docs deploy automatically on push to `main` via GitHub Actions. To enable this, go to your repo's Settings > Pages and set the source to **GitHub Actions**.

## Installation

```bash
uv add AirForm
```

## CLI

Preview rendered form HTML from any Pydantic model:

```bash
airform myapp.models:ContactModel
```

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup instructions.

## Author

AirForm was created in 2026 by Audrey M. Roy Greenfeld.

Built with [Cookiecutter](https://github.com/cookiecutter/cookiecutter) and the [audreyfeldroy/cookiecutter-pypackage](https://github.com/audreyfeldroy/cookiecutter-pypackage) project template.
