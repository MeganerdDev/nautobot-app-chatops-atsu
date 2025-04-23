"""App declaration for nautobot_chatops_atsu."""

# Metadata is inherited from Nautobot. If not including Nautobot in the environment, this should be added
from importlib import metadata

from nautobot.apps import NautobotAppConfig

__version__ = metadata.version(__name__)


class NautobotChatopsAtsuConfig(NautobotAppConfig):
    """App configuration for the nautobot_chatops_atsu app."""

    name = "nautobot_chatops_atsu"
    verbose_name = "Nautobot Chatops Atsu"
    version = __version__
    author = "meganerddev"
    description = "Nautobot Chatops Atsu."
    base_url = "atsu"
    required_settings = []
    min_version = "2.0.0"
    max_version = "2.9999"
    default_settings = {}
    caching_config = {}
    docs_view_name = "plugins:nautobot_chatops_atsu:docs"


config = NautobotChatopsAtsuConfig  # pylint:disable=invalid-name
