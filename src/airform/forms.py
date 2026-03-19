"""Display and Validation of HTML forms. Powered by pydantic.

Pro-tip: Always validate incoming data.

Extracted from air.forms. This module contains the framework-agnostic
parts: validation, error handling, and type mapping. The rendering
(default_form_widget, render, widget property) and async request
handling (from_request) stay in Air because they depend on Air's
tag system and Starlette's Request.
"""

from collections.abc import Sequence
from types import UnionType
from typing import Any, Union, get_args, get_origin

import annotated_types
from airfield import Autofocus, Label, Widget
from pydantic import BaseModel, ValidationError
from pydantic_core import ErrorDetails


class AirForm[M: BaseModel]:
    """A form handler that validates incoming form data against a Pydantic model.

    Example:

        from pydantic import BaseModel
        from airform import AirForm


        class FlightModel(BaseModel):
            flight_number: str
            destination: str


        class FlightForm(AirForm[FlightModel]):
            pass


        form = FlightForm()
        form.validate({"flight_number": "AA123", "destination": "Manila"})
        if form.is_valid:
            print(form.data.flight_number)
    """

    model: type[M] | None = None
    _data: M | None = None
    initial_data: dict | None = None
    errors: list[ErrorDetails] | None = None
    is_valid: bool = False
    includes: Sequence[str] | None = None

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if "model" not in cls.__dict__:
            for base in getattr(cls, "__orig_bases__", ()):
                if get_origin(base) is AirForm:
                    args = get_args(base)
                    if args and isinstance(args[0], type) and issubclass(args[0], BaseModel):
                        cls.model = args[0]
                        break

    def __init__(self, initial_data: dict | None = None) -> None:
        if self.model is None:
            msg = "model"
            raise NotImplementedError(msg)
        self.initial_data = initial_data

    @property
    def data(self) -> M:
        """The validated model instance.

        Raises:
            AttributeError: If accessed before successful validation.
        """
        if self._data is None:
            msg = "No validated data available. Check is_valid before accessing data."
            raise AttributeError(msg)
        return self._data

    def validate(self, form_data: dict[Any, Any]) -> bool:
        """Validate form data against the model.

        Args:
            form_data: Dictionary containing the form fields to validate

        Returns:
            True if validation succeeds, False otherwise
        """
        # Reset state from any previous validation
        self._data = None
        self.is_valid = False
        self.errors = None
        # Store the submitted data to preserve values on error
        self.submitted_data = dict(form_data) if hasattr(form_data, "items") else form_data
        try:
            assert self.model is not None
            self._data = self.model(**form_data)
            self.is_valid = True
        except ValidationError as e:
            self.errors = e.errors()
        return self.is_valid


def pydantic_type_to_html_type(field_info: Any) -> str:
    """Return HTML type from pydantic type.

    Checks field_info.metadata for a Widget instance (from AirField),
    then infers from the Python type annotation.
    """
    for m in getattr(field_info, "metadata", []):
        if isinstance(m, Widget):
            return m.kind

    return {int: "number", float: "number", bool: "checkbox", str: "text"}.get(field_info.annotation, "text")


def get_user_error_message(error: dict) -> str:
    """Convert technical pydantic error to user-friendly message.

    Returns:
        User-friendly error message string.
    """
    error_type = error.get("type", "")
    technical_msg = error.get("msg", "")

    # Map error types to user-friendly messages
    messages = {
        "missing": "This field is required.",
        "int_parsing": "Please enter a valid number.",
        "float_parsing": "Please enter a valid number.",
        "bool_parsing": "Please select a valid option.",
        "string_too_short": "This value is too short.",
        "string_too_long": "This value is too long.",
        "value_error": "This value is not valid.",
        "type_error": "Please enter the correct type of value.",
        "assertion_error": "This value doesn't meet the requirements.",
        "url_parsing": "Please enter a valid URL.",
        "email": "Please enter a valid email address.",
        "json_invalid": "Please enter valid JSON.",
        "enum": "Please select a valid option.",
        "greater_than": "This value must be greater than the minimum.",
        "greater_than_equal": "This value must be at least the minimum.",
        "less_than": "This value must be less than the maximum.",
        "less_than_equal": "This value must be at most the maximum.",
    }

    # Get user-friendly message or fallback to technical message
    return messages.get(error_type, technical_msg or "Please correct this error.")


def errors_to_dict(errors: list[dict] | None) -> dict[str, dict]:
    """Converts a pydantic error list to a dictionary for easier reference.

    Returns:
        Dictionary mapping field names to error details.
    """
    if errors is None:
        return {}
    return {error["loc"][0]: error for error in errors}


def label_for_field(field_name: str, field_info: Any) -> str:
    """Return the label for a field from AirField metadata."""
    for m in getattr(field_info, "metadata", []):
        if isinstance(m, Label):
            return m.text
    return field_name
