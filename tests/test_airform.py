"""Tests for AirForm: validation, error handling, and rendering.

Validation tests extracted from air/tests/test_forms.py. Rendering
tests exercise the full AirField metadata vocabulary that Daniel's
original default_form_widget didn't yet support.
"""

from typing import Annotated

import annotated_types
import pytest
from airfield import AirField
from pydantic import BaseModel, Field

from airform import AirForm, default_form_widget, errors_to_dict, get_user_error_message, pydantic_type_to_html_type

# ── Validation tests (from Air) ─────────────────────────────────────


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
    assert isinstance(form.data, JeepneyRouteModel)


def test_airform_data_before_validation_raises() -> None:
    class IslandModel(BaseModel):
        name: str

    class IslandForm(AirForm[IslandModel]):
        pass

    form = IslandForm()
    with pytest.raises(AttributeError, match="No validated data"):
        form.data  # noqa: B018


def test_airform_data_after_failed_validation_raises() -> None:
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
    class ModelA(BaseModel):
        x: str

    class ModelB(BaseModel):
        y: str

    class ExplicitForm(AirForm[ModelA]):
        model = ModelB

    assert ExplicitForm.model is ModelB


def test_airform_revalidation_resets_state() -> None:
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
    with pytest.raises(AttributeError, match="No validated data"):
        form.data  # noqa: B018


def test_airform_multi_level_inheritance() -> None:
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


# ── Render tests: Daniel's pattern + full AirField vocabulary ────────


def test_render_blank_form() -> None:
    class CheeseModel(BaseModel):
        name: str
        age: int

    class CheeseForm(AirForm[CheeseModel]):
        pass

    html = CheeseForm().render()
    assert '<label for="name">' in html
    assert "<input" in html
    assert 'name="name"' in html
    assert 'name="age"' in html
    assert 'type="number"' in html
    assert "required" in html


def test_render_with_initial_data() -> None:
    class CheeseModel(BaseModel):
        name: str
        age: int

    class CheeseForm(AirForm[CheeseModel]):
        pass

    html = CheeseForm({"name": "Cheddar", "age": 3}).render()
    assert 'value="Cheddar"' in html
    assert 'value="3"' in html


def test_render_preserves_submitted_data_on_error() -> None:
    class CheeseModel(BaseModel):
        name: str
        age: int

    class CheeseForm(AirForm[CheeseModel]):
        pass

    form = CheeseForm()
    form.validate({"name": "Brie", "age": "not-a-number"})
    assert not form.is_valid
    html = form.render()
    assert 'value="Brie"' in html
    assert 'aria-invalid="true"' in html
    assert "air-field-error" in html
    assert 'role="alert"' in html


def test_render_with_errors_shows_messages() -> None:
    class CheeseModel(BaseModel):
        name: str
        age: int

    class CheeseForm(AirForm[CheeseModel]):
        pass

    form = CheeseForm()
    form.validate({})
    html = form.render()
    assert "This field is required." in html


def test_render_with_includes() -> None:
    class PlaneModel(BaseModel):
        id: int
        name: str
        max_airspeed: str

    class PlaneForm(AirForm[PlaneModel]):
        includes = ("name", "max_airspeed")

    html = PlaneForm().render()
    assert 'name="name"' in html
    assert 'name="max_airspeed"' in html
    assert 'name="id"' not in html


def test_render_airfield_label() -> None:
    """Labels from AirField metadata appear in rendered HTML."""

    class CompanionModel(BaseModel):
        name: str = AirField(label="Companion Name")
        role: str = AirField(type="email", label="Missive Address")

    class CompanionForm(AirForm[CompanionModel]):
        pass

    html = CompanionForm().render()
    assert "Companion Name" in html
    assert "Missive Address" in html
    assert 'type="email"' in html


def test_render_airfield_placeholder() -> None:
    class CompanionModel(BaseModel):
        name: str = AirField(placeholder="e.g. Konstantina")

    class CompanionForm(AirForm[CompanionModel]):
        pass

    html = CompanionForm().render()
    assert 'placeholder="e.g. Konstantina"' in html


def test_render_airfield_help_text() -> None:
    class QuestModel(BaseModel):
        objective: str = AirField(
            widget="textarea",
            help_text="Be specific. 'Slay the dragon' is not a plan.",
        )

    class QuestForm(AirForm[QuestModel]):
        pass

    html = QuestForm().render()
    assert "<textarea" in html
    assert "air-field-help" in html
    assert "Be specific." in html


def test_render_airfield_choices() -> None:
    class CompanionModel(BaseModel):
        role: str = AirField(
            label="Party Role",
            choices=[
                ("tank", "The One Who Gets Hit"),
                ("healer", "The One Who Complains"),
                ("dps", "The One Who Takes Credit"),
                ("bard", "The One With Snacks"),
            ],
        )

    class CompanionForm(AirForm[CompanionModel]):
        pass

    html = CompanionForm().render()
    assert "<select" in html
    assert '<option value="tank">The One Who Gets Hit</option>' in html
    assert '<option value="bard">The One With Snacks</option>' in html
    assert '<option value="">-- Select --</option>' in html


def test_render_airfield_choices_with_selected() -> None:
    class CompanionModel(BaseModel):
        role: str = AirField(
            choices=[
                ("tank", "The One Who Gets Hit"),
                ("healer", "The One Who Complains"),
                ("dps", "The One Who Takes Credit"),
            ],
        )

    html = default_form_widget(model=CompanionModel, data={"role": "healer"})
    assert 'value="healer" selected' in html


def test_render_airfield_autofocus() -> None:
    class CompanionModel(BaseModel):
        name: str = AirField(label="Name", autofocus=True)

    class CompanionForm(AirForm[CompanionModel]):
        pass

    html = CompanionForm().render()
    assert "autofocus" in html


def test_render_airfield_primary_key_skipped() -> None:
    class CompanionModel(BaseModel):
        id: int | None = AirField(default=None, primary_key=True)
        name: str

    class CompanionForm(AirForm[CompanionModel]):
        pass

    html = CompanionForm().render()
    assert 'name="id"' not in html
    assert 'name="name"' in html


def test_render_airfield_textarea() -> None:
    class QuestModel(BaseModel):
        backstory: str = AirField(widget="textarea", placeholder="It all started in a tavern...")

    class QuestForm(AirForm[QuestModel]):
        pass

    html = QuestForm().render()
    assert "<textarea" in html
    assert 'placeholder="It all started in a tavern..."' in html


def test_render_airfield_textarea_with_value() -> None:
    class QuestModel(BaseModel):
        backstory: str = AirField(widget="textarea")

    html = default_form_widget(model=QuestModel, data={"backstory": "The wizard was late, as usual."})
    assert ">The wizard was late, as usual.</textarea>" in html


def test_render_checkbox() -> None:
    class WaiverModel(BaseModel):
        accepted: bool = AirField(default=False, label="I understand the dragon may eat me")

    class WaiverForm(AirForm[WaiverModel]):
        pass

    html = WaiverForm().render()
    assert 'type="checkbox"' in html
    # Label comes after input for checkboxes
    input_pos = html.index("<input")
    label_pos = html.index("<label")
    assert input_pos < label_pos


def test_render_optional_not_required() -> None:
    class CompanionModel(BaseModel):
        catchphrase: str | None = None

    class CompanionForm(AirForm[CompanionModel]):
        pass

    html = CompanionForm().render()
    assert "required" not in html


def test_render_min_max_length() -> None:
    class CompanionModel(BaseModel):
        name: str = AirField(min_length=2, max_length=50)

    class CompanionForm(AirForm[CompanionModel]):
        pass

    html = CompanionForm().render()
    assert 'minlength="2"' in html
    assert 'maxlength="50"' in html


def test_render_annotated_constraints() -> None:
    class CompanionModel(BaseModel):
        name: Annotated[str, annotated_types.MinLen(2), annotated_types.MaxLen(50)]

    class CompanionForm(AirForm[CompanionModel]):
        pass

    html = CompanionForm().render()
    assert 'minlength="2"' in html
    assert 'maxlength="50"' in html


def test_render_standard_field_constraints() -> None:
    class CompanionModel(BaseModel):
        name: str = Field(min_length=3, max_length=20)

    class CompanionForm(AirForm[CompanionModel]):
        pass

    html = CompanionForm().render()
    assert 'minlength="3"' in html
    assert 'maxlength="20"' in html


def test_custom_widget_swap() -> None:
    """Swappable widget pattern: replace the renderer."""

    class CompanionModel(BaseModel):
        name: str
        role: str

    def tavern_widget(*, model, data=None, errors=None, includes=None):
        return "<p>Fill this out or the barkeep gets cross.</p>"

    class CompanionForm(AirForm[CompanionModel]):
        widget = staticmethod(tavern_widget)

    html = CompanionForm().render()
    assert html == "<p>Fill this out or the barkeep gets cross.</p>"
