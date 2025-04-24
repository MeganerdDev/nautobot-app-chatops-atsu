"""Worker functions implementing Nautobot "atsu" command and subcommands."""

from ast import literal_eval
from typing import Any, Union

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db.models import Count
from django.utils.text import slugify
from nautobot.apps.config import get_app_settings_or_config
from nautobot.circuits.models import Circuit, CircuitTermination, CircuitType, Provider
from nautobot.dcim.models import Cable, Device, DeviceType, Location, LocationType, Manufacturer, Rack
from nautobot.dcim.models.device_components import FrontPort, Interface, RearPort
from nautobot.extras.choices import JobResultStatusChoices
from nautobot.extras.jobs import get_job
from nautobot.extras.models import Job, JobResult, Role, Status
from nautobot.ipam.choices import PrefixTypeChoices
from nautobot.ipam.models import Namespace, Prefix, VLAN, VLANGroup, RIR
from nautobot.tenancy.models import Tenant

from nautobot_chatops.choices import CommandStatusChoices 
#from nautobot_chatops.constants import CommandStatusChoices
from nautobot_chatops.workers import handle_subcommands, subcommand_of
from nautobot_chatops.workers.helper_functions import (
    add_asterisk,
    menu_item_check,
    menu_offset_value,
    nautobot_logo,
    prompt_for_circuit_filter_type,
    prompt_for_device_filter_type,
    prompt_for_interface_filter_type,
    prompt_for_vlan_filter_type,
) # pylint: disable=too-many-return-statements,too-many-branches

from nautobot_chatops.workers import subcommand_of, handle_subcommands
from .api.api import API as AtsuAPI
from .atsu import NautobotChatopsAtsu
from .helpers import parse_filters, prompt_for_prefix_filter_type, send_prefix_table


EXAMPLE_VAR = settings.PLUGINS_CONFIG["nautobot_chatops_atsu"].get("example_var")


def atsu(subcommand, **kwargs):
    """Interact with atsu app."""
    return handle_subcommands("atsu", subcommand, **kwargs)


# pylint: disable=too-many-statements
@subcommand_of("atsu")
def get_prefixes(dispatcher, filter_type=None, filter_value=None) -> Union[bool, CommandStatusChoices]:
    """Return a filtered list of Prefixes based on filter type and filter value.

    Args:
        dispatcher (Dispatcher): ChatOps dispatcher instance, for sending prompts and responses
        filter_type (Optional[str]): Category to filter by (e.g. "status", "role", "namespace", "all")
        filter_value (Optional[str]): Selected filter value or menu offset when prompting

    Returns:
        bool: False if awaiting user input (prompting from menu)
        CommandStatusChoices: STATUS_SUCCEEDED or STATUS_FAILED on completion
    """
    dispatcher.send_markdown(f"Command /atsu get-prefixes received with filter type '{filter_type}' and filter value '{filter_value}'")

    # create an instance of NautobotChatopsAtsu to suppress pylint
    NautobotChatopsAtsu()

    content_type = ContentType.objects.get_for_model(Prefix)

    if not filter_type:
        prompt_for_prefix_filter_type("nautobot get-prefixes", "Select a prefix filter", dispatcher)
        return False
    
    # normalize filter type
    filter_type = filter_type.lower()

    # prompt for menu choices if value if it was not provided
    if menu_item_check(filter_value):
        choices = []
        if filter_type == "all":
            prefixes = Prefix.objects.restrict(dispatcher.user, "view")
            dispatcher.send_blocks(
                dispatcher.command_response_header(
                    "nautobot",
                    "get-prefixes",
                    [("Filter type", filter_type)],
                    "Prefixes list",
                    nautobot_logo(dispatcher),
                )
            )
            send_prefix_table(dispatcher, prefixes, filter_type)
            return CommandStatusChoices.STATUS_SUCCEEDED
        elif filter_type == "status":
            choices = [(s.name, str(s.pk)) for s in Status.objects.get_for_model(Prefix)]
        elif filter_type == "role":
            choices = [(r.name, str(r.pk)) for r in Role.objects.filter(content_types=content_type)]
        elif filter_type == "namespace":
            choices = [(ns.name, str(ns.pk)) for ns in Namespace.objects.all()]
        elif filter_type == "vlan":
            choices = [
                (v.name, str(v.pk))
                for v in VLAN.objects.annotate(Count("prefixes")).filter(prefixes__count__gt=0)
            ]
        elif filter_type == "tenant":
            choices = [
                (t.name, str(t.pk))
                for t in Tenant.objects.annotate(Count("prefixes")).filter(prefixes__count__gt=0)
            ]
        elif filter_type == "rir":
            choices = [(r.name, str(r.pk)) for r in RIR.objects.annotate(Count("prefixes")).filter(prefixes__count__gt=0)]
        elif filter_type == "parent":
            choices = [(p.cidr_str, str(p.pk)) for p in Prefix.objects.filter(children__isnull=False)]
        elif filter_type == "type":
            choices = [
                (opt.label, opt.value) for opt in PrefixTypeChoices
            ]
        else:
            dispatcher.send_error(f"I don't know how to filter by {filter_type}")
            return (CommandStatusChoices.STATUS_FAILED, f"Unknown filter type \"{filter_type}\"")

        if not choices:
            dispatcher.send_error(f"No choices found for filter type {filter_type}")
            return (CommandStatusChoices.STATUS_FAILED, f"No choices for \"{filter_type}\"")

        dispatcher.prompt_from_menu(
            f"nautobot get-prefixes {filter_type}",
            f"Select a {filter_type}",
            choices,
            offset=menu_offset_value(filter_value),
        )
        return False

    if filter_type == "status":
        prefixes = Prefix.objects.restrict(dispatcher.user, "view").filter(status__pk=filter_value)
    elif filter_type == "role":
        prefixes = Prefix.objects.restrict(dispatcher.user, "view").filter(role__pk=filter_value)
    elif filter_type == "namespace":
        try:
            ns = Namespace.objects.get(pk=filter_value)
        except Namespace.DoesNotExist:
            dispatcher.send_error(f"Namespace {filter_value} not found")
            return (CommandStatusChoices.STATUS_FAILED, f"Namespace \"{filter_value}\" not found")
        prefixes = Prefix.objects.restrict(dispatcher.user, "view").filter(namespace=ns)
    elif filter_type == "vlan":
        try:
            vlan = VLAN.objects.get(pk=filter_value)
        except VLAN.DoesNotExist:
            dispatcher.send_error(f"VLAN {filter_value} not found")
            return (CommandStatusChoices.STATUS_FAILED, f"VLAN \"{filter_value}\" not found")
        prefixes = Prefix.objects.restrict(dispatcher.user, "view").filter(vlan=vlan)
    elif filter_type == "tenant":
        try:
            tenant = Tenant.objects.get(pk=filter_value)
        except Tenant.DoesNotExist:
            dispatcher.send_error(f"Tenant {filter_value} not found")
            return (CommandStatusChoices.STATUS_FAILED, f"Tenant \"{filter_value}\" not found")
        prefixes = Prefix.objects.restrict(dispatcher.user, "view").filter(tenant=tenant)
    elif filter_type == "rir":
        try:
            rir = RIR.objects.get(pk=filter_value)
        except RIR.DoesNotExist:
            dispatcher.send_error(f"RIR {filter_value} not found")
            return (CommandStatusChoices.STATUS_FAILED, f"RIR \"{filter_value}\" not found")
        prefixes = Prefix.objects.restrict(dispatcher.user, "view").filter(rir=rir)
    elif filter_type == "parent":
        try:
            parent = Prefix.objects.get(pk=filter_value)
        except Prefix.DoesNotExist:
            dispatcher.send_error(f"Prefix {filter_value} not found")
            return (CommandStatusChoices.STATUS_FAILED, f"Prefix \"{filter_value}\" not found")
        prefixes = Prefix.objects.filter(parent=parent)
    elif filter_type == "type":
        prefixes = Prefix.objects.restrict(dispatcher.user, "view").filter(type=filter_value)
    elif filter_type == "all":
        prefixes = Prefix.objects.restrict(dispatcher.user, "view")
    else:
        dispatcher.send_error(f"{filter_type} not supported")
        return (CommandStatusChoices.STATUS_FAILED, f"\"{filter_type}\" not supported")

    if not prefixes:
        dispatcher.send_error(f"No prefixes found for {filter_type} {filter_value}")
        return (CommandStatusChoices.STATUS_FAILED, f"No prefixes for \"{filter_type}\" \"{filter_value}\" found")

    dispatcher.send_blocks(
        dispatcher.command_response_header(
            "nautobot",
            "get-prefixes",
            [("Filter type", filter_type), ("Filter value 1", filter_value)],
            "Prefixes list",
            nautobot_logo(dispatcher),
        )
    )
    send_prefix_table(dispatcher, prefixes, filter_type)
    return CommandStatusChoices.STATUS_SUCCEEDED


# pylint: disable=too-many-statements
@subcommand_of("atsu")
def get_api(
    dispatcher,
    endpoint: str | None = None,
    raw_filters: str | None = None,
) -> Union[bool, CommandStatusChoices]:
    """Call Nautobot REST API via PyNautobot, using YAML definitions or raw args.

    Args:
        dispatcher (Dispatcher): ChatOps dispatcher instance for prompts and output
        endpoint (Optional[str]): YAML key (filename) or raw API path (e.g. "dcim.devices")
        raw_filters (Optional[str]): Python-dict string of filter params (e.g. '{"name": "site1"}')

    Returns:
        bool: False if awaiting user input (prompting)
        CommandStatusChoices: STATUS_SUCCEEDED or STATUS_FAILED on completion
    """
    cfg = get_app_settings_or_config("nautobot_chatops_atsu", {})
    nautobot_url = cfg.get("nautobot_url")
    nautobot_token = cfg.get("nautobot_token")
    if not nautobot_url or not nautobot_token:
        dispatcher.send_error("Missing 'nautobot_url' or 'nautobot_token' from nautobot_chatops_atsu PLUGINS config.")
        return CommandStatusChoices.STATUS_FAILED

    api_client = AtsuAPI(
        url=nautobot_url,
        token=nautobot_token
    )

    if not endpoint:
        choices = [(name, name) for name in api_client.endpoints]
        choices.append(("raw", "raw"))
        dispatcher.prompt_from_menu(
            "atsu get-api",
            "Select a predefined endpoint or choose 'raw'",
            choices,
        )
        return False

    if endpoint == "raw" and raw_filters is None:
        dispatcher.send_markdown("Enter the raw endpoint path (e.g. `dcim.devices`):")
        return False

    if raw_filters is None:
        dispatcher.send_markdown(f"Using endpoint `{endpoint}`, provide filters as a dict string or leave blank:")
        return False

    # parse the filter string into a dictionary
    filters: dict[str, Any] = {}
    if raw_filters.strip():
        try:
            filters = literal_eval(raw_filters)
        except Exception as exc:
            dispatcher.send_error(f"Invalid filter dict: {exc}")
            return CommandStatusChoices.STATUS_FAILED

    # perform the API call
    if endpoint in api_client.endpoints:
        dispatcher.send_markdown(f"Querying `{api_client.endpoints[endpoint]['endpoint']}` via YAML definition")
        result = api_client.action(endpoint)
    else:
        dispatcher.send_markdown(f"Querying `{endpoint}` with filters {filters}")
        nb = api_client.api
        for part in endpoint.split("."):
            nb = getattr(nb, part)
        result = nb.filter(**filters) if filters else nb.all()

    if not result:
        dispatcher.send_markdown("No results found")
        return CommandStatusChoices.STATUS_SUCCEEDED

    for obj in result:
        dispatcher.send_markdown(str(obj))

    return CommandStatusChoices.STATUS_SUCCEEDED
