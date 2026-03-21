# Usage

## Database-backed form (most common)

Most Air forms save to the database through AirModel. Define the model, create a form class, validate and save.

```python
from airmodel import AirModel, AirField
from airform import AirForm

class BookOrder(AirModel):
    id: int | None = AirField(default=None, primary_key=True)
    title: str = AirField(label="Book Title", min_length=1)
    quantity: int = AirField(label="Quantity", help_text="How many copies?")
    gift_wrap: bool = AirField(default=False, label="Gift wrap")

class BookOrderForm(AirForm[BookOrder]):
    pass
```

The `id` field is skipped in the rendered form because it has `primary_key=True`.

## Plain form (no database)

For forms that don't save to a database (contact forms, search, feedback), use a plain Pydantic `BaseModel`:

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
```

## Validate

```python
form = BookOrderForm()
form.validate({"title": "Everyone Dies", "quantity": "3"})

if form.is_valid:
    print(form.data.title)   # "Everyone Dies" — typed as str
    await BookOrder.create(**form.save_data())
```

After `validate()`:

- `form.is_valid` is `True` or `False`
- `form.data` is the validated model instance (raises `AttributeError` if not valid)
- `form.errors` is a list of Pydantic error dicts, or `None`
- `form.submitted_data` is the raw dict that was submitted

`validate()` accepts any `Mapping`, including Starlette's `FormData`.

## Render

```python
html = BookOrderForm().render()
```

Produces structured HTML with labels, inputs, accessibility attributes, error messages, and a CSRF token. PrimaryKey and Hidden("form") fields are auto-skipped.

## Validate from a request

In an Air web handler:

```python
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

With FastAPI dependency injection:

```python
from typing import Annotated
from fastapi import Depends

@app.post("/order")
async def submit(form: Annotated[BookOrderForm, Depends(BookOrderForm.from_request)]):
    if form.is_valid:
        await BookOrder.create(**form.save_data())
```

## Re-render with errors

When validation fails, `render()` preserves submitted values and shows error messages:

```python
form = BookOrderForm()
form.validate(submitted_data)  # fails
html = form.render()  # inputs keep their values, errors shown per field
```

Errors appear as `<div class="air-field-message" role="alert">` with `aria-invalid="true"` on the input.

## Excludes

Forms start with all fields and use `excludes` to hide what shouldn't appear. A bare string excludes from both rendering and `save_data()`. A tuple targets a specific scope:

```python
class ArticleForm(AirForm[Article]):
    excludes = (
        "created_at",              # hidden from display AND save_data()
        ("slug", "display"),       # hidden from form, still in save_data()
        ("internal_notes", "save"),  # rendered in form, excluded from save_data()
    )
```

PrimaryKey fields are display-excluded by default.

## save_data()

Returns validated data as a dict, excluding save-excluded fields:

```python
if form.is_valid:
    await Article.create(**form.save_data())
```

## Default stylesheet

AirForm ships CSS that styles every element it renders. Load it with:

```python
from airform import default_css

# In a Jinja2 template:
# <style>{{ default_css() }}</style>

# In Air tags:
# air.Style(default_css())
```

## CSRF protection

CSRF is automatic. `render()` embeds a signed hidden token. `validate()` after `render()` checks it. `from_request()` always enforces it. You don't configure anything.

For multi-worker production, set the `AIRFORM_SECRET` environment variable so all workers share the same signing key.

## Custom widget

Swap the renderer by setting `widget` on your form subclass:

```python
def my_renderer(*, model, data=None, errors=None, excludes=None):
    # Return an HTML string
    ...

class BookOrderForm(AirForm[BookOrder]):
    widget = staticmethod(my_renderer)
```

The CSRF hidden input is added by `render()` outside the widget, so custom widgets get CSRF protection for free.

## CLI preview

Preview rendered HTML for any importable model:

```bash
airform preview myapp.models:BookOrder
```
