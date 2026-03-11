"""
Terminal UI utilities for Testara
Beautiful colored output with ASCII art and rich formatting
"""
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich import box
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
import sys

console = Console()


TESTARA_BANNER = """
 ████████╗███████╗███████╗████████╗ █████╗ ██████╗  █████╗ 
 ╚══██╔══╝██╔════╝██╔════╝╚══██╔══╝██╔══██╗██╔══██╗██╔══██╗
    ██║   █████╗  ███████╗   ██║   ███████║██████╔╝███████║
    ██║   ██╔══╝  ╚════██║   ██║   ██╔══██║██╔══██╗██╔══██║
    ██║   ███████╗███████║   ██║   ██║  ██║██║  ██║██║  ██║
    ╚═╝   ╚══════╝╚══════╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝
"""


def print_banner():
    """Print Testara banner with gradient effect"""
    banner_text = Text(TESTARA_BANNER)
    banner_text.stylize("bold blue")
    
    panel = Panel(
        banner_text,
        title="[bold cyan]AI-Powered iOS Test Automation[/bold cyan]",
        subtitle="[dim]v2.0 • https://github.com/mheryerznkanyan/testara[/dim]",
        border_style="blue",
        box=box.DOUBLE
    )
    console.print(panel)
    console.print()


def print_step(step_num: int, total: int, title: str, status: str = ""):
    """Print a setup step with nice formatting"""
    if status == "done":
        icon = "[green]✓[/green]"
    elif status == "running":
        icon = "[yellow]►[/yellow]"
    elif status == "error":
        icon = "[red]✗[/red]"
    else:
        icon = "[dim]○[/dim]"
    
    console.print(f"{icon} [bold]Step {step_num}/{total}:[/bold] {title}")


def print_success(message: str):
    """Print success message"""
    console.print(f"[green]✓[/green] {message}")


def print_error(message: str):
    """Print error message"""
    console.print(f"[red]✗ Error:[/red] {message}", style="red")


def print_warning(message: str):
    """Print warning message"""
    console.print(f"[yellow]⚠[/yellow]  {message}")


def print_info(message: str):
    """Print info message"""
    console.print(f"[blue]ℹ[/blue]  {message}")


def print_config_table(config: dict):
    """Print configuration as a formatted table"""
    table = Table(
        title="[bold cyan]Configuration[/bold cyan]",
        box=box.ROUNDED,
        border_style="blue"
    )
    
    table.add_column("Setting", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")
    
    for key, value in config.items():
        # Mask sensitive values
        if "KEY" in key.upper() or "TOKEN" in key.upper():
            display_value = value[:10] + "..." if value else "[dim]not set[/dim]"
        else:
            display_value = value or "[dim]not set[/dim]"
        table.add_row(key, display_value)
    
    console.print(table)
    console.print()


def print_service_status(services: dict):
    """Print running services with URLs"""
    table = Table(
        title="[bold green]Services Running[/bold green]",
        box=box.ROUNDED,
        border_style="green"
    )
    
    table.add_column("Service", style="cyan", no_wrap=True)
    table.add_column("Status", style="green")
    table.add_column("URL", style="blue")
    
    for service, info in services.items():
        table.add_row(
            service,
            "[green]●[/green] Running",
            f"[link={info['url']}]{info['url']}[/link]"
        )
    
    console.print(table)
    console.print()
    console.print("[bold green]Testara is ready![/bold green] 🚀")
    console.print()


def create_spinner(text: str):
    """Create a spinner for long-running operations"""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True
    )


def print_indexing_progress(current: int, total: int, file: str):
    """Print indexing progress"""
    percent = (current / total) * 100 if total > 0 else 0
    bar_length = 30
    filled = int(bar_length * current / total) if total > 0 else 0
    bar = "█" * filled + "░" * (bar_length - filled)
    
    console.print(
        f"[cyan]Indexing:[/cyan] [{bar}] {percent:.1f}% ({current}/{total}) - {file}",
        end="\r"
    )


def print_completion():
    """Print completion message"""
    console.print()
    console.rule("[bold green]Setup Complete[/bold green]", style="green")
    console.print()


def print_separator():
    """Print a visual separator"""
    console.rule(style="dim")


def print_section_header(title: str):
    """Print a section header"""
    console.print()
    console.print(f"[bold cyan]{title}[/bold cyan]")
    console.print("─" * len(title), style="cyan")


if __name__ == "__main__":
    # Demo the terminal UI
    print_banner()
    
    print_section_header("Configuration")
    print_config_table({
        "ANTHROPIC_API_KEY": "sk_ant_1234567890",
        "PROJECT_ROOT": "/path/to/ios/app",
        "XCODE_PROJECT": "/path/to/project.xcodeproj"
    })
    
    print_section_header("Setup Steps")
    print_step(1, 5, "Check prerequisites", "done")
    print_step(2, 5, "Install dependencies", "done")
    print_step(3, 5, "Index iOS app", "running")
    print_step(4, 5, "Setup Xcode", "")
    print_step(5, 5, "Start services", "")
    
    console.print()
    print_success("Dependencies installed")
    print_warning("This is a warning message")
    print_error("This is an error message")
    print_info("This is an info message")
    
    console.print()
    print_service_status({
        "Backend": {"url": "http://localhost:8000"},
        "Frontend": {"url": "http://localhost:3000"}
    })
