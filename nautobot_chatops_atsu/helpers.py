"""Helper functions for worker."""

from typing import Any, Dict, List, Tuple, Union

from django.db.models.query import QuerySet
from nautobot.ipam.models import Prefix
#from nautobot.chatops.dispatcher import Dispatcher


def send_prefix_table(
    dispatcher,
    prefixes: QuerySet[Prefix],
    filter_type: str
) -> None:
    """Send a table of Prefix records."""
    dispatcher.send_markdown(f"**Showing prefixes filtered by '{filter_type}'**")

    headers = ["Prefix", "Status", "Role", "Namespace"]
    rows: list[list[str]] = []
    for prefix in prefixes:
        rows.append([
            prefix.cidr_str,
            prefix.status.name,
            prefix.role.name if prefix.role else "",
            prefix.namespace.name,
        ])

    header_line = "| " + " | ".join(headers) + " |"
    separator_line = "| " + " | ".join(["---"] * len(headers)) + " |"
    table_lines = [header_line, separator_line]
    for row in rows:
        table_lines.append("| " + " | ".join(row) + " |")

    markdown = "\n".join(table_lines)
    dispatcher.send_markdown(markdown)


def prompt_for_prefix_filter_type(
    action_id: str,
    help_text: str,
    dispatcher, #: Dispatcher,
) -> Any:
    """Prompt the user to select a valid Prefix filter type from a drop-down menu."""
    choices = [
        ("All (no filter)", "all"),
        ("Status", "status"),
        ("Role", "role"),
        ("Namespace", "namespace"),
        ("VLAN", "vlan"),
        ("Tenant", "tenant"),
        ("RIR", "rir"),
        ("Parent Prefix", "parent"),
        ("Type", "type"),
    ]
    return dispatcher.prompt_from_menu(action_id, help_text, choices)


class Mock_Dispatcher:
    """Mock chatops dispatcher for testing get_prefixes without mattermost/slack/teams."""
    def __init__(self, context: Dict[str, Any] = {}) -> None:
        self.context = context
        self.user = context.get("user", None)
        self.platform_name = context.get("platform_name", "mock")
        self.platform_slug = context.get("platform_slug", self.platform_name.lower())
        self.platform_color = context.get("platform_color", "000000")
        self.command_prefix = context.get("command_prefix", "/")
        self.sent_markdowns: list[str] = []
        self.sent_blocks: list[Any] = []
        self.prompts: list[tuple[str, str, list[tuple[str, str]], int]] = []
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.captured = {}

    def send_markdown(self, markdown: str) -> None:
        self.sent_markdowns.append(markdown)

    def send_blocks(self, blocks: Any) -> None:
        self.sent_blocks.append(blocks)

    def command_response_header(
        self,
        app: str,
        command: str,
        params: List[Tuple[str, str]],
        title: str,
        logo: Any
    ) -> Any:
        return {"app": app, "command": command, "params": params, "title": title}

    def prompt_from_menu(
        self,
        action_id: str,
        help_text: str,
        choices: List[Tuple[str, str]],
        offset: int = 0
    ) -> None:
        self.prompts.append((action_id, help_text, choices, offset))

    def send_error(self, message: str) -> None:
        self.errors.append(message)

    def send_warning(self, message: str) -> None:
        self.warnings.append(message)

    def bold(self, text: str) -> str:
        return f"*{text}*"

    def image_element(self, image_url: str, alt_text: str | None = None) -> dict:
        element = {"type": "image", "url": image_url}
        if alt_text:
            element["alt"] = alt_text
        return element

    def static_url(self, path: str) -> str:
        return path


class Capture_Dispatcher(Mock_Dispatcher):

    def __init__(self, context: dict = {}):
        super().__init__(context=context)
        self.captured["disp"] = self
