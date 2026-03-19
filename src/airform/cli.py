"""Console script for airform."""

import typer
from rich.console import Console

from airform import utils

app = typer.Typer()
console = Console()


@app.command()
def main() -> None:
    """Console script for airform."""
    console.print("Replace this message by putting your code into airform.cli.main")
    console.print("See Typer documentation at https://typer.tiangolo.com/")
    utils.do_something_useful()


if __name__ == "__main__":
    app()
