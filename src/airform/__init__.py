"""AirForm: Display and Validation of HTML forms. Powered by pydantic.

Pro-tip: Always validate incoming data."""

from importlib.metadata import version

from airform.forms import (
    AirForm,
    SafeHTML,
    default_form_widget,
    errors_to_dict,
    get_user_error_message,
    label_for_field,
    pydantic_type_to_html_type,
)
from airform.styles import default_css

__version__ = version("airform")

__all__ = [
    "AirForm",
    "SafeHTML",
    "default_css",
    "default_form_widget",
    "errors_to_dict",
    "get_user_error_message",
    "label_for_field",
    "pydantic_type_to_html_type",
]
