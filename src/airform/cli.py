"""Console script for airform.

Preview rendered form HTML from a Pydantic model:

    airform preview myapp:ContactModel
"""

import importlib

import typer
from rich.console import Console
from rich.syntax import Syntax

from airform import default_form_widget

app = typer.Typer()
console = Console()


@app.command()
def preview(model_path: str) -> None:
    """Render a Pydantic model as form HTML and print it.

    MODEL_PATH is module:ClassName, e.g. myapp.models:ContactModel
    """
    module_name, _, class_name = model_path.rpartition(":")
    if not module_name or not class_name:
        console.print(f"[red]Expected module:ClassName, got {model_path!r}[/red]")
        raise typer.Exit(1)

    module = importlib.import_module(module_name)
    model = getattr(module, class_name)
    html = default_form_widget(model=model)
    console.print(Syntax(html, "html", theme="monokai"))


if __name__ == "__main__":
    app()
