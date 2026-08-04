"""Colored markdown stdio helpers for Goal CLI output."""

from __future__ import annotations

import click

from goal.git_ops import HAS_CLICKMD, echo_md

_markdown_mode = False


def set_stdio_markdown(enabled: bool) -> None:
    """Enable or disable markdown-formatted stdio for the current workflow."""
    global _markdown_mode
    _markdown_mode = bool(enabled)


def use_markdown_stdio() -> bool:
    """Return True when markdown stdio (via clickmd) should be used."""
    return _markdown_mode and HAS_CLICKMD


def echo_via_markdown(text: str) -> None:
    """Render markdown when enabled, otherwise plain text."""
    if use_markdown_stdio():
        echo_md(text)
    else:
        click.echo(text)


def echo_heading(text: str, *, level: int = 2) -> None:
    if use_markdown_stdio():
        echo_md(f"\n{'#' * level} {text}\n")
    else:
        click.echo(click.style(text, fg="cyan", bold=True))


def echo_auto(text: str) -> None:
    if use_markdown_stdio():
        echo_md(f"\n**🤖 AUTO:** {text}\n")
    else:
        click.echo(click.style(f"\n🤖 AUTO: {text}", fg="cyan"))


def echo_command_block(command: str, *, language: str = "bash") -> None:
    if use_markdown_stdio():
        echo_md(f"```{language}\n{command}\n```")
    else:
        click.echo(click.style(f"  → {command}", fg="bright_black"))


def echo_output_block(output: str, *, language: str = "text") -> None:
    if not output:
        return
    if use_markdown_stdio():
        echo_md(f"```{language}\n{output.rstrip()}\n```")
    else:
        click.echo(output.rstrip())


def echo_info(text: str) -> None:
    if use_markdown_stdio():
        echo_md(text)
    else:
        click.echo(text)


def echo_status_ok(text: str) -> None:
    if use_markdown_stdio():
        echo_md(f"✅ {text}")
    else:
        click.echo(click.style(f"✓ {text}", fg="green", bold=True))


def echo_status_warn(text: str) -> None:
    if use_markdown_stdio():
        echo_md(f"⚠️ {text}")
    else:
        click.echo(click.style(f"⚠ {text}", fg="yellow"))


def echo_status_error(text: str) -> None:
    if use_markdown_stdio():
        echo_md(f"❌ {text}")
    else:
        click.echo(click.style(text, fg="red", bold=True))
