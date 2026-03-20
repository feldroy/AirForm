# /// script
# requires-python = ">=3.12"
# dependencies = ["airform", "airfield"]
# ///
"""Pottery workshop registration form built from AGENTS.md documentation alone."""

from pydantic import BaseModel
from airfield import AirField
from airform import AirForm


# 1. Define the data model with AirField metadata
class PotteryRegistration(BaseModel):
    name: str = AirField(
        min_length=1,
        label="Potter's Name",
        placeholder="e.g. Audrey M. Roy Greenfeld",
        autofocus=True,
    )
    email: str = AirField(min_length=1, type="email", label="Email")
    experience: str = AirField(
        choices=[
            ("beginner", "Beginner"),
            ("intermediate", "Intermediate"),
            ("advanced", "Advanced"),
        ]
    )
    project: str = AirField(
        default="",
        widget="textarea",
        label="What do you want to make?",
        help_text="We have wheels, kilns, and hand-building stations.",
    )
    bring_own_clay: bool = AirField(default=False, label="I'll bring my own clay")


# 2. Create the form class (one line, as AGENTS.md says)
class PotteryForm(AirForm[PotteryRegistration]):
    pass


def separator(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}\n")


# --- 2. Render a blank form and print the HTML ---
separator("BLANK FORM")
blank_form = PotteryForm()
blank_html = blank_form.render()
print(blank_html)


# --- 3. Validate a good submission and print the validated data ---
separator("GOOD SUBMISSION")
good_data = {
    "name": "Audrey M. Roy Greenfeld",
    "email": "audreyfeldroy@example.com",
    "experience": "advanced",
    "project": "A raku-fired tea bowl",
    "bring_own_clay": True,
}

good_form = PotteryForm()
good_form.validate(good_data)
assert good_form.is_valid, f"Expected valid, got errors: {good_form.errors}"

print(f"Name:      {good_form.data.name}")
print(f"Email:     {good_form.data.email}")
print(f"Exp:       {good_form.data.experience}")
print(f"Project:   {good_form.data.project}")
print(f"Own clay:  {good_form.data.bring_own_clay}")


# --- 4. Validate a bad submission and print the errors ---
separator("BAD SUBMISSION (missing required fields)")
bad_data = {
    "name": "",
    "email": "",
    "experience": "beginner",
}

bad_form = PotteryForm()
bad_form.validate(bad_data)
assert not bad_form.is_valid, "Expected invalid"
print("Errors:")
for error in bad_form.errors:
    print(f"  - {error}")


# --- 5. Re-render with errors preserved ---
separator("RE-RENDERED FORM WITH ERRORS")
error_html = bad_form.render()
print(error_html)

# Verify that aria-invalid appears in the re-rendered HTML (AGENTS.md says it should)
assert "aria-invalid" in error_html, "Expected aria-invalid in re-rendered HTML"
print("\n(aria-invalid attribute confirmed present)")
