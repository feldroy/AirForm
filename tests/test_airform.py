"""Tests for AirForm, extracted from air/tests/test_forms.py.

Only the framework-agnostic parts: validation, error handling, type
mapping. Tests that depend on Air tags, Starlette Request, or FastAPI
Depends stay in Air.
"""

from typing import Annotated

import annotated_types
import pytest
from pydantic import BaseModel, Field

from airform import AirForm, errors_to_dict, get_user_error_message, pydantic_type_to_html_type


def test_form_sync_check() -> None:
    class CheeseModel(BaseModel):
        name: str
        age: int

    class CheeseForm(AirForm):
        model = CheeseModel

    cheese = CheeseForm()
    cheese.validate({"name": "Parmesan", "age": "Hello"})
    assert cheese.is_valid is False
    assert cheese.errors == [
        {
            "type": "int_parsing",
            "loc": ("age",),
            "msg": "Input should be a valid integer, unable to parse string as an integer",
            "input": "Hello",
            "url": "https://errors.pydantic.dev/2.12/v/int_parsing",
        },
    ]


def test_airform_notimplementederror() -> None:
    with pytest.raises(NotImplementedError) as exc:
        AirForm()

    assert "model" in str(exc.value)


def test_airform_validate() -> None:
    class KareKareModel(BaseModel):
        name: str
        servings: int

    class KareKareForm(AirForm):
        model = KareKareModel

    form = KareKareForm()
    assert not form.is_valid
    form.validate({})
    assert not form.is_valid
    form.validate({"name": "Kare-Kare"})
    assert not form.is_valid
    form.validate({"name": "Kare-Kare", "servings": 4})
    assert form.is_valid
    assert form.errors is None


def test_airform_generic_validates() -> None:
    class AutoModel(BaseModel):
        name: str
        age: int

    class AutoForm(AirForm[AutoModel]):
        pass

    form = AutoForm()
    form.validate({"name": "Test", "age": 3})
    assert form.is_valid is True


def test_airform_generic_type_parameter() -> None:
    """AirForm[M] sets model from the type parameter and makes form.data typed as M."""

    class JeepneyRouteModel(BaseModel):
        route_name: str
        origin: str
        destination: str

    class JeepneyRouteForm(AirForm[JeepneyRouteModel]):
        pass

    assert JeepneyRouteForm.model is JeepneyRouteModel

    form = JeepneyRouteForm()
    form.validate({"route_name": "01C", "origin": "Antipolo", "destination": "Cubao"})
    assert form.is_valid

    assert form.data.route_name == "01C"
    assert form.data.origin == "Antipolo"
    assert form.data.destination == "Cubao"
    assert isinstance(form.data, JeepneyRouteModel)


def test_airform_data_before_validation_raises() -> None:
    """Accessing form.data before validation raises AttributeError."""

    class IslandModel(BaseModel):
        name: str

    class IslandForm(AirForm[IslandModel]):
        pass

    form = IslandForm()
    with pytest.raises(AttributeError, match="No validated data"):
        form.data  # noqa: B018


def test_airform_data_after_failed_validation_raises() -> None:
    """Accessing form.data after failed validation raises AttributeError."""

    class IslandModel(BaseModel):
        name: str

    class IslandForm(AirForm[IslandModel]):
        pass

    form = IslandForm()
    form.validate({})
    assert not form.is_valid
    with pytest.raises(AttributeError, match="No validated data"):
        form.data  # noqa: B018


def test_airform_explicit_model_not_overridden() -> None:
    """Explicit model = X in class body takes priority over type parameter."""

    class ModelA(BaseModel):
        x: str

    class ModelB(BaseModel):
        y: str

    class ExplicitForm(AirForm[ModelA]):
        model = ModelB

    assert ExplicitForm.model is ModelB


def test_airform_revalidation_resets_state() -> None:
    """Calling validate() a second time clears stale data from the first call."""

    class SariSariModel(BaseModel):
        item: str
        price: int

    class SariSariForm(AirForm[SariSariModel]):
        pass

    form = SariSariForm()

    form.validate({"item": "Chicharon", "price": 25})
    assert form.is_valid
    assert form.data.item == "Chicharon"

    form.validate({})
    assert not form.is_valid
    assert form.errors is not None
    with pytest.raises(AttributeError, match="No validated data"):
        form.data  # noqa: B018


def test_airform_multi_level_inheritance() -> None:
    """Model propagates through multi-level class inheritance."""

    class BarangayModel(BaseModel):
        name: str
        captain: str

    class BaseBarangayForm(AirForm[BarangayModel]):
        pass

    class SpecificBarangayForm(BaseBarangayForm):
        pass

    assert SpecificBarangayForm.model is BarangayModel

    form = SpecificBarangayForm()
    form.validate({"name": "San Antonio", "captain": "Kap. Reyes"})
    assert form.is_valid
    assert form.data.captain == "Kap. Reyes"


def test_airform_generic_data_access() -> None:
    """AirForm[M] gives typed data after validation."""

    class PalengkeModel(BaseModel):
        vendor: str
        stall_number: int

    class PalengkeForm(AirForm[PalengkeModel]):
        pass

    form = PalengkeForm()
    form.validate({"vendor": "Aling Nena", "stall_number": 42})
    assert form.is_valid
    assert form.data.vendor == "Aling Nena"
    assert form.data.stall_number == 42


# ── Helper function tests ───────────────────────────────────────────


def test_get_user_error_message() -> None:
    assert get_user_error_message({"type": "missing"}) == "This field is required."
    assert get_user_error_message({"type": "int_parsing"}) == "Please enter a valid number."
    assert get_user_error_message({"type": "unknown", "msg": "Some error"}) == "Some error"
    assert get_user_error_message({"type": "unknown"}) == "Please correct this error."


def test_errors_to_dict() -> None:
    errors = [
        {"type": "missing", "loc": ("name",), "msg": "Field required"},
        {"type": "int_parsing", "loc": ("age",), "msg": "Invalid integer"},
    ]
    result = errors_to_dict(errors)
    assert "name" in result
    assert "age" in result
    assert result["name"]["type"] == "missing"


def test_errors_to_dict_none() -> None:
    assert errors_to_dict(None) == {}


def test_pydantic_type_to_html_type() -> None:
    class TestModel(BaseModel):
        name: str
        age: int
        score: float
        active: bool

    assert pydantic_type_to_html_type(TestModel.model_fields["name"]) == "text"
    assert pydantic_type_to_html_type(TestModel.model_fields["age"]) == "number"
    assert pydantic_type_to_html_type(TestModel.model_fields["score"]) == "number"
    assert pydantic_type_to_html_type(TestModel.model_fields["active"]) == "checkbox"
