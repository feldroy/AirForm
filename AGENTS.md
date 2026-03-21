# AGENTS.md

You are working with AirForm, a Python library that turns Pydantic models into validated, rendered HTML forms. It reads presentation metadata from AirField and produces accessible HTML with zero configuration.

Most Air forms save to the database through AirModel. Some forms do something else (send an email, trigger an API call, run a search). AirForm handles both.

## Database-backed forms (most common)

The typical case: the form fields match a database model. Use AirModel directly.

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

# Validate and save
form = BookOrderForm()
form.validate({"title": "Everyone Dies", "quantity": "3"})
if form.is_valid:
    await BookOrder.create(
        title=form.data.title,
        quantity=form.data.quantity,
        gift_wrap=form.data.gift_wrap,
    )

# Render a blank form
html = BookOrderForm().render()
```

The `id` field is skipped in the form because it has `primary_key=True`.

## Plain forms (no database)

For forms that don't save to a database, use a plain Pydantic `BaseModel`. Contact forms, search forms, login forms, feedback forms.

```python
from pydantic import BaseModel
from airfield import AirField
from airform import AirForm

class ContactMessage(BaseModel):
    name: str = AirField(label="Your Name", autofocus=True)
    email: str = AirField(type="email", label="Email")
    message: str = AirField(widget="textarea", label="Message")

class ContactForm(AirForm[ContactMessage]):
    pass

form = ContactForm()
form.validate({"name": "Audrey", "email": "audreyfeldroy@example.com", "message": "Hello!"})
if form.is_valid:
    send_email(form.data.name, form.data.email, form.data.message)
```

## What AirField metadata does

AirField wraps `pydantic.Field` and adds presentation metadata that AirForm reads when rendering:

| AirField parameter | What it does in the rendered HTML |
|---|---|
| `label="Display Name"` | `<label>` text (default: field name title-cased) |
| `type="email"` | `<input type="email">` |
| `widget="textarea"` | `<textarea>` instead of `<input>` |
| `placeholder="hint..."` | `placeholder` attribute |
| `help_text="explanation"` | Help text div below the input |
| `choices=[("val","Label")]` | `<select>` with `<option>` elements |
| `autofocus=True` | `autofocus` attribute |
| `primary_key=True` | Field is skipped in form rendering |
| `min_length=N` | `minlength="N"` HTML5 attribute |
| `max_length=N` | `maxlength="N"` HTML5 attribute |

## Async: from_request()

The typical web handler pattern with AirModel:

```python
import air
from airmodel import AirModel, AirField
from airform import AirForm

app = air.Air()

class BookOrder(AirModel):
    id: int | None = AirField(default=None, primary_key=True)
    title: str = AirField(label="Book Title", min_length=1)
    quantity: int = AirField(label="Quantity")

class BookOrderForm(AirForm[BookOrder]):
    pass

@app.page
def order_page(request: air.Request) -> air.Html:
    return air.Html(
        air.H1("Order a Book"),
        air.Form(
            air.Raw(BookOrderForm().render()),
            air.Button("Order", type_="submit"),
            method="post", action="/order",
        ),
    )

@app.post("/order")
async def submit_order(request: air.Request) -> air.Html:
    form = await BookOrderForm.from_request(request)
    if form.is_valid:
        await BookOrder.create(
            title=form.data.title,
            quantity=form.data.quantity,
        )
        return air.Html(air.H1(f"Ordered: {form.data.title}"))
    return air.Html(
        air.H1("Please fix the errors"),
        air.Form(
            air.Raw(form.render()),  # re-render with errors + preserved values
            air.Button("Order", type_="submit"),
            method="post", action="/order",
        ),
    )
```

`from_request()` reads `request.form()`, validates with CSRF, and returns the populated form. Works with FastAPI's `Depends` for dependency injection.

## The validation flow

```python
form = MyForm()
form.validate({"name": "Audrey", "email": "audreyfeldroy@example.com"})
```

After `validate()`:
- `form.is_valid` is `True` or `False`
- `form.data` is the validated model instance (raises `AttributeError` if not valid)
- `form.errors` is a list of Pydantic error dicts, or `None`
- `form.submitted_data` is the raw dict that was submitted

Calling `validate()` again resets all state. No stale data leaks between calls.

## The render flow

```python
html = form.render()
```

`render()` produces HTML string with:
- A hidden CSRF token (automatic, signed with HMAC)
- One `<div class="air-field">` per field containing label, input, and optional help text
- `aria-invalid="true"` and error messages on fields that failed validation
- Checkboxes with the label after the input
- PrimaryKey and Hidden("form") fields skipped automatically

If `validate()` was called before `render()`, submitted values and errors are preserved in the re-rendered form.

## CSRF protection

CSRF is automatic. You don't configure it, you don't add fields to your model, you don't think about it.

- `render()` embeds a signed token as a hidden input
- `validate()` after `render()` checks the token through Pydantic's validation (it uses a wrapper model internally)
- `validate()` without a prior `render()` skips CSRF (this is for programmatic use and tests)
- `from_request()` always enforces CSRF (browser submissions come from rendered forms)
- `form.data` never has a `csrf_token` attribute; it's stripped before you see it

For multi-worker production, set `AIRFORM_SECRET` env var so all workers share the same signing key. Otherwise a per-process key is auto-generated.

## Form models vs database models

When the form fields match the database model, use the AirModel directly:

```python
class BookOrder(AirModel):
    id: int | None = AirField(default=None, primary_key=True)
    title: str = AirField(label="Title")

class BookOrderForm(AirForm[BookOrder]):
    pass
```

When the form needs extra fields (confirm_password, terms checkbox) or different validation, define a separate form model with plain `BaseModel`:

```python
from pydantic import BaseModel

class UserRegistration(BaseModel):
    """Form model, not the database model."""
    username: str = AirField(label="Username", min_length=3)
    email: str = AirField(type="email", label="Email")
    password: str = AirField(type="password", label="Password", min_length=8)
    confirm_password: str = AirField(type="password", label="Confirm Password")

class RegistrationForm(AirForm[UserRegistration]):
    pass

class User(AirModel):
    """Database model, different fields."""
    id: int | None = AirField(default=None, primary_key=True)
    username: str
    email: str
    password_hash: str
```

## Custom rendering

Swap the entire renderer by setting `widget` on your form class:

```python
def my_renderer(*, model, data=None, errors=None, includes=None):
    # Build HTML however you want
    return "<div>my custom form</div>"

class BookOrderForm(AirForm[BookOrder]):
    widget = staticmethod(my_renderer)
```

The widget receives the model class, pre-populated data, validation errors, and an optional field filter. It returns an HTML string. The CSRF hidden input is added by `render()` outside the widget, so custom widgets get CSRF protection for free.

## Common patterns

**Subset of fields:**
```python
class ShippingForm(AirForm[Order]):
    includes = ("address", "city", "zip_code")
```

**Pre-populated edit form:**
```python
form = BookOrderForm({"title": "Existing Book", "quantity": 2})
html = form.render()  # inputs have values filled in
```

**Re-render after validation errors:**
```python
form = BookOrderForm()
form.validate(submitted_data)  # fails
html = form.render()  # shows errors + preserves submitted values
```

## What NOT to do

- Don't instantiate `AirForm` directly. Always subclass it: `class MyForm(AirForm[MyModel]): pass`
- Don't access `form.data` before calling `validate()` or after failed validation (it raises `AttributeError`)
- Don't put `csrf_token` on your Pydantic model. AirForm handles it internally.
- Don't import from `airform.forms` or `airform.csrf` directly unless you're building a custom integration. Use the top-level `from airform import AirForm` exports.

## Architecture (for understanding, not for using)

- `airfield` package defines presentation metadata types (Widget, Label, Choices, etc.) as frozen dataclasses on `field_info.metadata`
- `airmodel` package provides the async ORM (AirModel extends BaseModel with database operations, re-exports AirField)
- `airform` reads AirField metadata and produces HTML. It's a consumer of AirField's vocabulary.
- The renderer walks `model.model_fields`, builds a `{type: instance}` dict of metadata per field for O(1) lookup, and produces the appropriate HTML element
- CSRF uses a Pydantic wrapper model created at class definition time via `create_model`. The wrapper inherits from your model and adds a `csrf_token: ValidCsrfToken` field. `ValidCsrfToken` is a custom Pydantic type that validates the HMAC signature in `__get_pydantic_core_schema__`
