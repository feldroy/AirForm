# AirForm

![PyPI version](https://img.shields.io/pypi/v/AirForm.svg)

Pydantic-native form validation and rendering for [Air](https://airwebframework.org/). Define an AirModel, get a validated, rendered HTML form with CSRF protection.

* GitHub: https://github.com/feldroy/AirForm/
* PyPI package: https://pypi.org/project/AirForm/
* Created by: **[Audrey M. Roy Greenfeld](https://audrey.feldroy.com/)** | GitHub https://github.com/audreyfeldroy | PyPI https://pypi.org/user/audreyr/
* Free software: MIT License

## Features

* Type-safe validated data via `AirForm[MyModel]` generic parameter
* Works with [AirModel](https://github.com/feldroy/AirModel) (database-backed forms) and plain BaseModel (contact forms, search, etc.)
* Reads the full [AirField](https://github.com/feldroy/AirField) metadata vocabulary: Widget, Label, Placeholder, HelpText, Choices, Autofocus, PrimaryKey, Hidden, ReadOnly
* Auto-skips PrimaryKey and Hidden("form") fields in rendered output
* HTML5 validation attributes from Pydantic constraints (minlength, maxlength, required)
* Accessible by default: aria-invalid, aria-describedby, role="alert" on errors
* Textarea, select, and checkbox rendering from type annotations and metadata
* Zero-config CSRF protection: render() embeds a signed token, validate() checks it
* Scoped excludes: hide fields from display, saving, or both
* `save_data()` returns a dict ready for `await MyModel.create()`
* `default_css()` built-in stylesheet for polished forms without a CSS framework
* Swappable widget for custom renderers
* `from_request()` for async ASGI request handling (works with FastAPI Depends)

## Quick start

### Database-backed form (most common)

```python
from airmodel import AirModel, AirField
from airform import AirForm
import air

app = air.Air()

class BookOrder(AirModel):
    id: int | None = AirField(default=None, primary_key=True)
    title: str = AirField(label="Book Title", min_length=1)
    quantity: int = AirField(label="Quantity")

class BookOrderForm(AirForm[BookOrder]):
    pass

@app.page
def order_page(request: air.Request):
    return air.Html(
        air.H1("Order a Book"),
        air.Form(
            BookOrderForm().render(),
            air.Button("Order", type_="submit"),
            method="post", action="/order",
        ),
    )

@app.post("/order")
async def submit_order(request: air.Request):
    form = await BookOrderForm.from_request(request)
    if form.is_valid:
        await BookOrder.create(**form.save_data())
        return air.Html(air.H1(f"Ordered: {form.data.title}"))
    return air.Html(
        air.Form(
            form.render(),
            air.Button("Order", type_="submit"),
            method="post", action="/order",
        ),
    )
```

### Plain form (no database)

```python
from pydantic import BaseModel
from airfield import AirField
from airform import AirForm

class ContactMessage(BaseModel):
    name: str = AirField(label="Name", autofocus=True)
    email: str = AirField(type="email", label="Email")
    message: str = AirField(widget="textarea", label="Message")

class ContactForm(AirForm[ContactMessage]):
    pass

form = ContactForm()
form.validate({"name": "Audrey", "email": "audreyfeldroy@example.com", "message": "Hello!"})
if form.is_valid:
    send_email(form.data.name, form.data.email, form.data.message)

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
airform preview myapp.models:ContactModel
```

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup instructions.

## Author

AirForm was created in 2026 by Audrey M. Roy Greenfeld, extending Daniel Roy Greenfeld's original [form rendering design](https://github.com/feldroy/air/commit/de07dbf) from Air.

Built with [Cookiecutter](https://github.com/cookiecutter/cookiecutter) and the [audreyfeldroy/cookiecutter-pypackage](https://github.com/audreyfeldroy/cookiecutter-pypackage) project template.
