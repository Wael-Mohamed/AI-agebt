#!/usr/bin/env python3
"""
AI Sales Agent — Multi-Agent Sales System
==========================================
Agents:
  Orchestrator  → routes every request to the right specialist
  Qualifier     → BANT lead scoring and stage assignment
  Outreach      → personalized email drafting
  ObjectionHandler → Feel-Felt-Found objection responses
  Closer        → closing strategies for hot leads
  Analyzer      → pipeline health + strategic recommendations
"""

import os
import sys

import anthropic
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich import box

from config import ANTHROPIC_API_KEY
from tools.crm_tools import CRMStore
from agents.orchestrator import OrchestratorAgent

console = Console()

AGENT_COLORS = {
    "orchestrator": "cyan",
    "qualifier": "yellow",
    "outreach": "blue",
    "objection": "magenta",
    "closer": "green",
    "analyzer": "red",
}

HELP_TEXT = """
[bold]Available commands:[/bold]

  [cyan]add lead[/cyan]          → Add a new lead (guided)
  [cyan]pipeline[/cyan]          → Show pipeline overview
  [cyan]analyze[/cyan]           → Run pipeline analysis
  [cyan]qualify <lead_id>[/cyan] → Qualify a specific lead
  [cyan]email <lead_id>[/cyan]   → Draft outreach email
  [cyan]close <lead_id>[/cyan]   → Execute closing strategy
  [cyan]help[/cyan]              → Show this help
  [cyan]quit / exit[/cyan]       → Exit

Or just type naturally — the Orchestrator will route your request.

[dim]Examples:[/dim]
  "The lead from Acme Corp says they don't have budget right now"
  "Draft a follow-up email for lead abc12345"
  "Which leads should I focus on today?"
"""

WELCOME_BANNER = """
╔══════════════════════════════════════════════════════╗
║          AI SALES AGENT — MULTI-AGENT SYSTEM         ║
║                                                      ║
║  Qualifier · Outreach · Objection · Closer · Analyst ║
╚══════════════════════════════════════════════════════╝
"""


def show_pipeline(crm: CRMStore) -> None:
    summary = crm.get_pipeline_summary()
    pipeline = summary["pipeline"]

    table = Table(title="Sales Pipeline", box=box.ROUNDED, show_lines=True)
    table.add_column("Stage", style="bold")
    table.add_column("Count", justify="center")
    table.add_column("Leads")

    stage_colors = {
        "NEW": "white", "QUALIFYING": "yellow", "NURTURING": "blue",
        "PROPOSAL": "cyan", "NEGOTIATION": "magenta",
        "CLOSED_WON": "green", "CLOSED_LOST": "red",
    }

    for stage, leads in pipeline.items():
        color = stage_colors.get(stage, "white")
        names = ", ".join(f"{l['name']} ({l['company']})" for l in leads) if leads else "—"
        table.add_row(f"[{color}]{stage}[/{color}]", str(len(leads)), names)

    console.print(table)
    console.print(f"[dim]Total leads: {summary['total_leads']}[/dim]\n")


def add_lead_guided(crm: CRMStore) -> str:
    console.print("\n[bold cyan]Add New Lead[/bold cyan]")
    name = Prompt.ask("Full name")
    company = Prompt.ask("Company")
    email = Prompt.ask("Email")
    lead = crm.create_lead(name, company, email)
    console.print(f"[green]✓ Lead created — ID: [bold]{lead.id}[/bold][/green]\n")
    return lead.id


def print_agent_response(agent_name: str, response: str) -> None:
    color = AGENT_COLORS.get(agent_name, "white")
    title = f"[{color}]{agent_name.upper()}[/{color}]"
    console.print(Panel(response, title=title, border_style=color, padding=(1, 2)))


def run_interactive(orchestrator: OrchestratorAgent, crm: CRMStore) -> None:
    console.print(f"[bold green]{WELCOME_BANNER}[/bold green]")
    console.print(HELP_TEXT)

    while True:
        try:
            user_input = Prompt.ask("\n[bold white]You[/bold white]").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Goodbye![/dim]")
            break

        if not user_input:
            continue

        cmd = user_input.lower()

        if cmd in ("quit", "exit", "q"):
            console.print("[dim]Goodbye![/dim]")
            break

        if cmd == "help":
            console.print(HELP_TEXT)
            continue

        if cmd in ("pipeline", "show pipeline", "p"):
            show_pipeline(crm)
            continue

        if cmd in ("add lead", "new lead", "add"):
            lead_id = add_lead_guided(crm)
            console.print(f"[dim]Tip: type 'qualify {lead_id}' to qualify this lead[/dim]")
            continue

        if cmd == "analyze":
            user_input = "Analyze the full pipeline and provide a health report with top priorities."

        elif cmd.startswith("qualify "):
            lead_id = cmd.split("qualify ", 1)[1].strip()
            user_input = f"Qualify lead {lead_id} based on all available information."

        elif cmd.startswith("email "):
            lead_id = cmd.split("email ", 1)[1].strip()
            user_input = f"Draft an outreach email for lead {lead_id}."

        elif cmd.startswith("close "):
            lead_id = cmd.split("close ", 1)[1].strip()
            user_input = f"Execute closing strategy for lead {lead_id}."

        with console.status("[dim]Routing to best agent...[/dim]", spinner="dots"):
            try:
                agent_name, response = orchestrator.route(user_input)
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
                continue

        print_agent_response(agent_name, response)


def main() -> None:
    if not ANTHROPIC_API_KEY:
        console.print(
            "[red]Error: ANTHROPIC_API_KEY not set.\n"
            "Create a .env file with: ANTHROPIC_API_KEY=your_key_here[/red]"
        )
        sys.exit(1)

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    crm = CRMStore()
    orchestrator = OrchestratorAgent(client, crm)

    # Seed a demo lead so the system is ready to demo immediately
    demo = crm.create_lead("Sarah Chen", "Acme Corp", "sarah@acmecorp.com")
    demo.notes = "VP of Engineering. Mentioned scaling problems and 50-person eng team."

    run_interactive(orchestrator, crm)


if __name__ == "__main__":
    main()
