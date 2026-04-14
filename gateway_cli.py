#!/usr/bin/env python3
"""
OEE IoT Gateway — CLI Device Manager

A command-line interface for managing counting and inspection devices
on the OEE IoT Gateway. Talks to the FastAPI backend API so all
validation, business logic, and MQTT hot-reload are shared with the
web dashboard.

Usage:
    python gateway_cli.py [OPTIONS] COMMAND [ARGS]

Examples:
    python gateway_cli.py status
    python gateway_cli.py --api-url http://192.168.100.249:8000 counting list
    python gateway_cli.py counting add
    python gateway_cli.py counting delete 3
"""

import sys
import json as json_lib
from typing import Optional

import requests
import typer
from rich import print as rprint
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

# ─── App & State ────────────────────────────────────────────────

app = typer.Typer(
    name="gateway-cli",
    help="OEE IoT Gateway — CLI Device Manager",
    no_args_is_help=True,
    rich_markup_mode="rich",
)

counting_app = typer.Typer(
    name="counting",
    help="Manage [bold cyan]counting[/bold cyan] devices (production throughput counters)",
    no_args_is_help=True,
    rich_markup_mode="rich",
)

inspection_app = typer.Typer(
    name="inspection",
    help="Manage [bold magenta]inspection[/bold magenta] devices (quality control sensors)",
    no_args_is_help=True,
    rich_markup_mode="rich",
)

app.add_typer(counting_app, name="counting")
app.add_typer(inspection_app, name="inspection")

console = Console(force_terminal=True)

# Global state set by callback
_api_url: str = "http://localhost:8000"
_json_output: bool = False


@app.callback()
def main_callback(
    api_url: str = typer.Option(
        "http://localhost:8000",
        "--api-url",
        "-u",
        help="Backend API base URL",
        envvar="GATEWAY_API_URL",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output raw JSON (for scripting)",
    ),
):
    """Configure global options."""
    global _api_url, _json_output
    _api_url = api_url.rstrip("/")
    _json_output = json_output


# ─── API Client ─────────────────────────────────────────────────

def api_request(method: str, path: str, data: dict = None) -> dict | list:
    """Make an HTTP request to the gateway API."""
    url = f"{_api_url}{path}"
    try:
        resp = requests.request(method, url, json=data, timeout=10)
    except requests.ConnectionError:
        console.print(f"[bold red]X[/] Cannot connect to [cyan]{_api_url}[/]")
        console.print("  Is the gateway backend running?")
        raise typer.Exit(1)
    except requests.Timeout:
        console.print(f"[bold red]X[/] Request timed out: [cyan]{url}[/]")
        raise typer.Exit(1)

    if resp.status_code == 404:
        console.print("[bold red]X[/] Not found - check the device ID")
        raise typer.Exit(1)
    if resp.status_code == 422:
        detail = resp.json().get("detail", "Validation error")
        console.print(f"[bold red]X[/] Validation error: {detail}")
        raise typer.Exit(1)
    if resp.status_code >= 400:
        detail = resp.json().get("detail", resp.text)
        console.print(f"[bold red]X[/] Error {resp.status_code}: {detail}")
        raise typer.Exit(1)

    # DELETE returns a message dict, others return data
    return resp.json()


def print_json(data):
    """Print raw JSON when --json flag is set."""
    console.print_json(json_lib.dumps(data, default=str))


# ─── Status Command ─────────────────────────────────────────────

@app.command()
def status():
    """Show gateway health and device counts."""
    data = api_request("GET", "/api/status")

    if _json_output:
        print_json(data)
        return

    # Format uptime
    secs = data.get("uptime_seconds", 0)
    h, rem = divmod(int(secs), 3600)
    m, s = divmod(rem, 60)
    uptime = f"{h}h {m}m {s}s" if h else f"{m}m {s}s" if m else f"{s}s"

    mqtt_status = "[bold green]* Online[/]" if data.get("mqtt_connected") else "[bold red]* Offline[/]"

    panel = Panel(
        f"  MQTT Connection   {mqtt_status}\n"
        f"  Counting Nodes    [bold]{data.get('counting_devices', 0)}[/]\n"
        f"  Inspection Nodes  [bold]{data.get('inspection_devices', 0)}[/]\n"
        f"  Uptime            [dim]{uptime}[/]",
        title=f"[bold]OEE Gateway - {data.get('gateway_id', '?')}[/]",
        border_style="blue",
        padding=(1, 2),
    )
    console.print(panel)


# ─── Counting Device Commands ────────────────────────────────────

@counting_app.command("list")
def counting_list():
    """List all counting devices."""
    devices = api_request("GET", "/api/devices")

    if _json_output:
        print_json(devices)
        return

    if not devices:
        console.print("[dim]No counting devices configured.[/]")
        return

    table = Table(title="Counting Devices", border_style="blue")
    table.add_column("ID", style="dim", width=5)
    table.add_column("Node ID", style="bold cyan")
    table.add_column("Cloud UID", max_width=24)
    table.add_column("OK Ch.", justify="center")
    table.add_column("NG Ch.", justify="center")
    table.add_column("Active", justify="center")
    table.add_column("Gateway", style="dim")

    for d in devices:
        active = "[green]Yes[/]" if d["is_active"] else "[red]No[/]"
        table.add_row(
            str(d["id"]),
            d["node_id"],
            d["cloud_uid"],
            str(d["ok_channel"]),
            str(d["ng_channel"]),
            active,
            d.get("gateway_id", ""),
        )

    console.print(table)


@counting_app.command("get")
def counting_get(
    device_id: int = typer.Argument(..., help="Device ID to retrieve"),
):
    """Get a single counting device by ID."""
    device = api_request("GET", f"/api/devices/{device_id}")

    if _json_output:
        print_json(device)
        return

    _print_device_detail(device, "counting")


@counting_app.command("add")
def counting_add(
    node_id: Optional[str] = typer.Option(None, "--node-id", "-n", help="Node ID (e.g. C071)"),
    cloud_uid: Optional[str] = typer.Option(None, "--cloud-uid", "-c", help="Cloud device UID"),
    device_secret: Optional[str] = typer.Option(None, "--device-secret", "-s", help="HMAC device secret"),
    ok_channel: int = typer.Option(0, "--ok-channel", help="OK channel number"),
    ng_channel: int = typer.Option(1, "--ng-channel", help="NG channel number"),
    active: bool = typer.Option(True, "--active/--inactive", help="Device active state"),
):
    """Add a new counting device. Prompts interactively if args are omitted."""
    if not node_id:
        node_id = typer.prompt("Node ID", type=str)
    if not cloud_uid:
        cloud_uid = typer.prompt("Cloud UID", type=str)
    if not device_secret:
        device_secret = typer.prompt("Device Secret", type=str, hide_input=True)

    payload = {
        "node_id": node_id,
        "cloud_uid": cloud_uid,
        "device_secret": device_secret,
        "ok_channel": ok_channel,
        "ng_channel": ng_channel,
        "is_active": active,
    }

    result = api_request("POST", "/api/devices", data=payload)

    if _json_output:
        print_json(result)
        return

    console.print(f"[bold green]OK[/] Created counting device [cyan]{result['node_id']}[/] (id={result['id']})")


@counting_app.command("update")
def counting_update(
    device_id: int = typer.Argument(..., help="Device ID to update"),
    node_id: Optional[str] = typer.Option(None, "--node-id", "-n", help="New node ID"),
    cloud_uid: Optional[str] = typer.Option(None, "--cloud-uid", "-c", help="New cloud UID"),
    device_secret: Optional[str] = typer.Option(None, "--device-secret", "-s", help="New device secret"),
    ok_channel: Optional[int] = typer.Option(None, "--ok-channel", help="New OK channel"),
    ng_channel: Optional[int] = typer.Option(None, "--ng-channel", help="New NG channel"),
    active: Optional[bool] = typer.Option(None, "--active/--inactive", help="Set active state"),
):
    """Update a counting device. Only specified fields are changed."""
    # Fetch current state
    current = api_request("GET", f"/api/devices/{device_id}")

    # Merge updates
    payload = {
        "node_id": node_id if node_id is not None else current["node_id"],
        "cloud_uid": cloud_uid if cloud_uid is not None else current["cloud_uid"],
        "device_secret": device_secret if device_secret is not None else current["device_secret"],
        "ok_channel": ok_channel if ok_channel is not None else current["ok_channel"],
        "ng_channel": ng_channel if ng_channel is not None else current["ng_channel"],
        "is_active": active if active is not None else current["is_active"],
    }

    result = api_request("PUT", f"/api/devices/{device_id}", data=payload)

    if _json_output:
        print_json(result)
        return

    console.print(f"[bold green]OK[/] Updated counting device [cyan]{result['node_id']}[/] (id={result['id']})")


@counting_app.command("delete")
def counting_delete(
    device_id: int = typer.Argument(..., help="Device ID to delete"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompt"),
):
    """Delete a counting device."""
    if not force:
        # Show what we're about to delete
        device = api_request("GET", f"/api/devices/{device_id}")
        confirm = typer.confirm(
            f"Delete counting device {device['node_id']} (id={device['id']})?",
            default=False,
        )
        if not confirm:
            console.print("[dim]Cancelled.[/]")
            raise typer.Exit(0)

    api_request("DELETE", f"/api/devices/{device_id}")

    if _json_output:
        print_json({"message": "Deleted", "id": device_id})
        return

    console.print(f"[bold green]OK[/] Deleted counting device (id={device_id})")


# ─── Inspection Device Commands ──────────────────────────────────

@inspection_app.command("list")
def inspection_list():
    """List all inspection devices."""
    devices = api_request("GET", "/api/inspectors")

    if _json_output:
        print_json(devices)
        return

    if not devices:
        console.print("[dim]No inspection devices configured.[/]")
        return

    table = Table(title="Inspection Devices", border_style="magenta")
    table.add_column("ID", style="dim", width=5)
    table.add_column("Node ID", style="bold magenta")
    table.add_column("Cloud UID", max_width=24)
    table.add_column("Sensors", justify="center", style="cyan bold")
    table.add_column("Active", justify="center")
    table.add_column("Gateway", style="dim")

    for d in devices:
        active = "[green]Yes[/]" if d["is_active"] else "[red]No[/]"
        table.add_row(
            str(d["id"]),
            d["node_id"],
            d["cloud_uid"],
            str(d["total_sensor"]),
            active,
            d.get("gateway_id", ""),
        )

    console.print(table)


@inspection_app.command("get")
def inspection_get(
    device_id: int = typer.Argument(..., help="Device ID to retrieve"),
):
    """Get a single inspection device by ID."""
    device = api_request("GET", f"/api/inspectors/{device_id}")

    if _json_output:
        print_json(device)
        return

    _print_device_detail(device, "inspection")


@inspection_app.command("add")
def inspection_add(
    node_id: Optional[str] = typer.Option(None, "--node-id", "-n", help="Node ID (e.g. Q005)"),
    cloud_uid: Optional[str] = typer.Option(None, "--cloud-uid", "-c", help="Cloud device UID"),
    device_secret: Optional[str] = typer.Option(None, "--device-secret", "-s", help="HMAC device secret"),
    total_sensor: int = typer.Option(1, "--total-sensor", "-t", help="Number of sensors"),
    active: bool = typer.Option(True, "--active/--inactive", help="Device active state"),
):
    """Add a new inspection device. Prompts interactively if args are omitted."""
    if not node_id:
        node_id = typer.prompt("Node ID", type=str)
    if not cloud_uid:
        cloud_uid = typer.prompt("Cloud UID", type=str)
    if not device_secret:
        device_secret = typer.prompt("Device Secret", type=str, hide_input=True)

    payload = {
        "node_id": node_id,
        "cloud_uid": cloud_uid,
        "device_secret": device_secret,
        "total_sensor": total_sensor,
        "is_active": active,
    }

    result = api_request("POST", "/api/inspectors", data=payload)

    if _json_output:
        print_json(result)
        return

    console.print(f"[bold green]OK[/] Created inspection device [magenta]{result['node_id']}[/] (id={result['id']})")


@inspection_app.command("update")
def inspection_update(
    device_id: int = typer.Argument(..., help="Device ID to update"),
    node_id: Optional[str] = typer.Option(None, "--node-id", "-n", help="New node ID"),
    cloud_uid: Optional[str] = typer.Option(None, "--cloud-uid", "-c", help="New cloud UID"),
    device_secret: Optional[str] = typer.Option(None, "--device-secret", "-s", help="New device secret"),
    total_sensor: Optional[int] = typer.Option(None, "--total-sensor", "-t", help="New sensor count"),
    active: Optional[bool] = typer.Option(None, "--active/--inactive", help="Set active state"),
):
    """Update an inspection device. Only specified fields are changed."""
    current = api_request("GET", f"/api/inspectors/{device_id}")

    payload = {
        "node_id": node_id if node_id is not None else current["node_id"],
        "cloud_uid": cloud_uid if cloud_uid is not None else current["cloud_uid"],
        "device_secret": device_secret if device_secret is not None else current["device_secret"],
        "total_sensor": total_sensor if total_sensor is not None else current["total_sensor"],
        "is_active": active if active is not None else current["is_active"],
    }

    result = api_request("PUT", f"/api/inspectors/{device_id}", data=payload)

    if _json_output:
        print_json(result)
        return

    console.print(f"[bold green]OK[/] Updated inspection device [magenta]{result['node_id']}[/] (id={result['id']})")


@inspection_app.command("delete")
def inspection_delete(
    device_id: int = typer.Argument(..., help="Device ID to delete"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompt"),
):
    """Delete an inspection device."""
    if not force:
        device = api_request("GET", f"/api/inspectors/{device_id}")
        confirm = typer.confirm(
            f"Delete inspection device {device['node_id']} (id={device['id']})?",
            default=False,
        )
        if not confirm:
            console.print("[dim]Cancelled.[/]")
            raise typer.Exit(0)

    api_request("DELETE", f"/api/inspectors/{device_id}")

    if _json_output:
        print_json({"message": "Deleted", "id": device_id})
        return

    console.print(f"[bold green]OK[/] Deleted inspection device (id={device_id})")


# ─── Shared Helpers ──────────────────────────────────────────────

def _print_device_detail(device: dict, device_type: str):
    """Pretty-print a single device's detail view."""
    color = "cyan" if device_type == "counting" else "magenta"
    active = "[green]Active[/]" if device["is_active"] else "[red]Inactive[/]"

    lines = [
        f"  [bold]Node ID[/]        [{color}]{device['node_id']}[/{color}]",
        f"  [bold]Cloud UID[/]      {device['cloud_uid']}",
        f"  [bold]Secret[/]         {'*' * 8}{device['device_secret'][-4:]}",
    ]

    if device_type == "counting":
        lines.append(f"  [bold]OK Channel[/]     {device['ok_channel']}")
        lines.append(f"  [bold]NG Channel[/]     {device['ng_channel']}")
    else:
        lines.append(f"  [bold]Total Sensors[/]  {device['total_sensor']}")

    lines.append(f"  [bold]Status[/]         {active}")
    lines.append(f"  [bold]Gateway[/]        [dim]{device.get('gateway_id', '')}[/]")
    lines.append(f"  [bold]Created[/]        [dim]{device.get('created_at', '')}[/]")
    lines.append(f"  [bold]Updated[/]        [dim]{device.get('updated_at', '')}[/]")

    panel = Panel(
        "\n".join(lines),
        title=f"[bold]{device_type.title()} Device #{device['id']}[/]",
        border_style=color,
        padding=(1, 2),
    )
    console.print(panel)


# ─── Entrypoint ──────────────────────────────────────────────────

if __name__ == "__main__":
    app()
