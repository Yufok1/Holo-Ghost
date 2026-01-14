"""
HOLO-GHOST - Main Entry Point

CLI and daemon launcher.
"""

import asyncio
import click
from rich.console import Console
from rich.panel import Panel

from holo_ghost import HoloGhost, Config, __version__

console = Console()


def banner():
    """Print the Ghost banner."""
    console.print(Panel.fit(
        """[bold cyan]
    ██╗  ██╗ ██████╗ ██╗      ██████╗       ██████╗ ██╗  ██╗ ██████╗ ███████╗████████╗
    ██║  ██║██╔═══██╗██║     ██╔═══██╗     ██╔════╝ ██║  ██║██╔═══██╗██╔════╝╚══██╔══╝
    ███████║██║   ██║██║     ██║   ██║     ██║  ███╗███████║██║   ██║███████╗   ██║   
    ██╔══██║██║   ██║██║     ██║   ██║     ██║   ██║██╔══██║██║   ██║╚════██║   ██║   
    ██║  ██║╚██████╔╝███████╗╚██████╔╝     ╚██████╔╝██║  ██║╚██████╔╝███████║   ██║   
    ╚═╝  ╚═╝ ╚═════╝ ╚══════╝ ╚═════╝       ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝   ╚═╝   
[/bold cyan]
    [dim]The Digital Holy Ghost - I see what you do.[/dim]
    """,
        border_style="cyan"
    ))


@click.group()
@click.version_option(version=__version__)
def cli():
    """HOLO-GHOST - System-agnostic input observer & intelligence layer."""
    pass


@cli.command()
@click.option('--config', '-c', type=click.Path(), help='Path to config file')
@click.option('--overlay/--no-overlay', default=False, help='Show in-game overlay')
@click.option('--llm/--no-llm', default=True, help='Enable LLM intelligence')
@click.option('--record/--no-record', default=True, help='Enable clip recording')
def start(config, overlay, llm, record):
    """Start the HOLO-GHOST daemon."""
    banner()
    
    # Load config
    cfg = Config.load(config) if config else Config.load()
    cfg.llm.enabled = llm
    cfg.recorder.enabled = record
    
    console.print(f"[cyan]Loading configuration...[/cyan]")
    console.print(f"  • LLM: {'[green]enabled[/green]' if llm else '[red]disabled[/red]'}")
    console.print(f"  • Recording: {'[green]enabled[/green]' if record else '[red]disabled[/red]'}")
    console.print(f"  • Overlay: {'[green]enabled[/green]' if overlay else '[red]disabled[/red]'}")
    
    # Create and start Ghost
    ghost = HoloGhost(config=cfg)
    
    async def run():
        if await ghost.start():
            console.print("\n[bold green]👻 HOLO-GHOST is watching...[/bold green]")
            console.print("[dim]Press Ctrl+C to stop[/dim]\n")
            
            try:
                # Keep running
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                console.print("\n[yellow]Stopping...[/yellow]")
                await ghost.stop()
        else:
            console.print("[red]Failed to start HOLO-GHOST[/red]")
    
    asyncio.run(run())


@cli.command()
def status():
    """Check HOLO-GHOST daemon status."""
    console.print("[yellow]Status check not yet implemented (daemon mode)[/yellow]")


@cli.command()
@click.argument('question', nargs=-1)
def ask(question):
    """Ask the Ghost a question."""
    if not question:
        console.print("[red]Please provide a question[/red]")
        return
    
    question_text = ' '.join(question)
    console.print(f"[cyan]Asking: {question_text}[/cyan]")
    console.print("[yellow]Interactive mode not yet implemented[/yellow]")


@cli.command()
@click.option('--output', '-o', type=click.Path(), help='Output path for config')
def init(output):
    """Initialize a new configuration file."""
    cfg = Config()
    
    if output:
        cfg.save(output)
        console.print(f"[green]Config saved to: {output}[/green]")
    else:
        cfg.save()
        console.print("[green]Config saved to: ~/.holo_ghost/config.yaml[/green]")


@cli.command()
@click.argument('receipt_hash')
def verify(receipt_hash):
    """Verify a session receipt hash."""
    from holo_ghost.provenance import ProvenanceChain
    
    chain = ProvenanceChain()
    result = chain.verify_receipt(receipt_hash)
    
    if result:
        console.print(f"[green]✓ Receipt verified![/green]")
        console.print(f"  Session: {result['session_id']}")
        console.print(f"  Started: {result['started_at']}")
        console.print(f"  Ended: {result['ended_at']}")
    else:
        console.print(f"[red]✗ Receipt not found in chain[/red]")


def main():
    """Entry point."""
    cli()


if __name__ == "__main__":
    main()
