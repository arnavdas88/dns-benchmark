from typing import List
from typing_extensions import Annotated

import typer

from rich.console import Console
from rich.live import Live
from rich.table import Table

console = Console()

app = typer.Typer(no_args_is_help=True)
benchmark_app = typer.Typer(no_args_is_help=True)
app.add_typer(benchmark_app, name="benchmark")

from .dns_utils import benchmark

@benchmark_app.command("realtime")
def realtime(
    domain: Annotated[List[str], typer.Option(default_factory=list)]
):
    """
    Test square rootiness. Call from the command line with:

        dns_benchmark benchmark realtime --domain=microsoft.com --domain=x.com 
    """

    with Live(console=console, refresh_per_second=4) as live:
        for _ in range(20):
            # https://rich.readthedocs.io/en/latest/live.html
            # https://github.com/Textualize/rich/blob/master/examples/table_movie.py

            data = benchmark(console=console, additional_domains=domain, N=2)
            sorted_data = sorted(data, key=lambda data: data['mean'])

            console.clear()
            console.print(sorted_data)
    
    # return benchmark(console=console, additional_domains=domain)
