import time
from typing import Annotated

import typer

from template_service.core import package_version

app = typer.Typer(help="Python Docker Service Template command-line tools.")


@app.callback(invoke_without_command=True)
def main(
    version: Annotated[bool, typer.Option("--version", help="Show the installed version and exit.")] = False,
) -> None:
    if version:
        typer.echo(package_version())
        raise typer.Exit


@app.command()
def health() -> None:
    typer.echo("ok")


@app.command()
def serve(
    interval_seconds: Annotated[int, typer.Option("--interval-seconds", min=1)] = 60,
) -> None:
    while True:
        time.sleep(interval_seconds)
