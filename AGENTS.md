# AGENTS.md

You are working with AirForm, a Python library that turns Pydantic models into validated, rendered HTML forms. It reads presentation metadata from AirField and produces accessible HTML with zero configuration.

## The mental model

There are three things: a **model** (your data), a **form class** (the bridge), and **two operations** (validate and render).

```python
from pydantic import BaseModel
from airfield import AirField
from airform import AirForm

# 1. Define your data as a Pydantic model with AirField metadata
class BookOrder(BaseModel):
    title: str = AirField(label="Book Title", min_length=1)
    quantity: int = AirField(label="Quantity", help_text="How many copies?")
    gift_wrap: bool = AirField(default=False, label="Gift wrap")

# 2. Create a form class (one line)
class BookOrderForm(AirForm[BookOrder]):
    pass

# 3a. Validate
form = BookOrderForm()
form.validate({"title": "Everyone Dies", "quantity": "3"})
if form.is_valid:
    print(form.data.title)  # "Everyone Dies" — typed as str

# 3b. Render
html = BookOrderForm().render()  # complete HTML with labels, inputs, CSRF token
```

That's the whole API.

## What AirField metadata does

AirField wraps `pydantic.Field` and adds presentation metadata that AirForm reads when rendering. You don't have to use AirField, plain `str` and `int` annotations work, but AirField gives you control over how fields appear:

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

## The validation flow

```python
form = MyForm()
form.validate({"name": "Audrey", "email": "audreyfeldroy@example.com"})
```

After `validate()`:
- `form.is_valid` is `True` or `False`
- `form.data` is the validated Pydantic model instance (raises `AttributeError` if not valid)
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

## Async: from_request()

For web handlers that receive form submissions:

```python
@app.post("/order")
async def submit(request):
    form = await BookOrderForm.from_request(request)
    if form.is_valid:
        save_order(form.data)
        return success_page(form.data.title)
    return render_form_page(form.render())  # re-render with errors
```

`from_request()` reads `request.form()` (Starlette/FastAPI), validates with CSRF, and returns the populated form. Works with FastAPI's `Depends` for dependency injection.

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
- `airform` reads that metadata and produces HTML. It's a consumer of AirField's vocabulary.
- The renderer walks `model.model_fields`, builds a `{type: instance}` dict of metadata per field for O(1) lookup, and produces the appropriate HTML element
- CSRF uses a Pydantic wrapper model created at class definition time via `create_model`. The wrapper inherits from your model and adds a `csrf_token: ValidCsrfToken` field. `ValidCsrfToken` is a custom Pydantic type that validates the HMAC signature in `__get_pydantic_core_schema__`
