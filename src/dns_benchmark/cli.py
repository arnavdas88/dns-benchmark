from typing import List, Optional
from typing_extensions import Annotated, Literal

from pathlib import Path
import json

import typer

from rich.console import Console
from rich.live import Live

console = Console()

app = typer.Typer(no_args_is_help=True)
benchmark = typer.Typer(no_args_is_help=True)

app.add_typer(benchmark, name = "benchmark")

from . import dns_utils

TimeUnitKeys = [k.name for k in dns_utils.TimeUnit]
# TimeUnitLiteral = Literal[*TimeUnitKeys]

@benchmark.command()
def server(
    domain: Annotated[List[str], typer.Option(default_factory=list)],
    server: Annotated[List[str], typer.Option(default_factory=list)],
    samples: int = typer.Option(default=50),
    time_unit: Literal["s", "ms", "us", "ns"] = typer.Option(default="ms"),
    export: Annotated[Optional[Path], typer.Option(exists=True, file_okay=True, dir_okay=False, writable=True)] = None,
):
    """
    Test square rootiness. Call from the command line with:

        dns_benchmark benchmark server --domain=microsoft.com --domain=x.com --samples=100 --time-unit=ms
    """

    if export:
        if export.is_dir():
            typer.echo("--export points to a directory. Needs to be a file.", err=True)
            typer.Exit()
            exit()

        if not export.parent.exists():
            try:
                export.parent.mkdir(parents=True, exist_ok=True)
            except Exception as ex:
                typer.echo(ex, err=True)
                typer.Exit()
                exit()


    with Live(console=console, screen=False, auto_refresh=False, ) as live:
        # https://rich.readthedocs.io/en/latest/live.html
        # https://github.com/Textualize/rich/blob/master/examples/table_movie.py

        data = dns_utils.benchmark(console=live, additional_domains=domain, additional_servers=server, N=samples, time_unit=time_unit)

    if export:
        with open(export, "w") as file:
            json.dump(data, file)

@benchmark.command()
def domain():
    typer.echo("Not Implemented Yet.", err=True)
    typer.Exit()
    exit()