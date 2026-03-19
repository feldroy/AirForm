# Usage

## Define a model and form

```python
from pydantic import BaseModel
from airfield import AirField
from airform import AirForm

class ContactModel(BaseModel):
    name: str
    email: str = AirField(type="email", label="Email Address")
    message: str = AirField(widget="textarea", placeholder="Your message...")

class ContactForm(AirForm[ContactModel]):
    pass
```

## Validate

```python
form = ContactForm()
form.validate({"name": "Audrey", "email": "audreyfeldroy@example.com", "message": "Hello!"})

if form.is_valid:
    print(form.data.name)   # "Audrey" — typed as str
    print(form.data.email)  # autocomplete works
```

## Render

```python
html = ContactForm().render()
```

Produces structured HTML with labels, inputs, accessibility attributes, and error messages. PrimaryKey and Hidden("form") fields are auto-skipped.

## Validate from a request

Works with any ASGI framework (Starlette, FastAPI, Litestar):

```python
@app.post("/contact")
async def submit(request):
    form = await ContactForm.from_request(request)
    if form.is_valid:
        send_email(form.data.name, form.data.email, form.data.message)
```

With FastAPI dependency injection:

```python
from typing import Annotated
from fastapi import Depends

@app.post("/contact")
async def submit(form: Annotated[ContactForm, Depends(ContactForm.from_request)]):
    if form.is_valid:
        send_email(form.data.name, form.data.email, form.data.message)
```

## Custom widget

Swap the renderer by setting `widget` on your form subclass:

```python
def my_renderer(*, model, data=None, errors=None, includes=None):
    # Return an HTML string
    ...

class ContactForm(AirForm[ContactModel]):
    widget = staticmethod(my_renderer)
```

## CLI preview

Preview rendered HTML for any importable model:

```bash
airform myapp.models:ContactModel
```
