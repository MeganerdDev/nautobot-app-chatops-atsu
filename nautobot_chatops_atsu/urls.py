from django.urls import path
from django.views.generic import TemplateView
from . import views

app_name = "nautobot_chatops_atsu"

urlpatterns = [
    path(
        "",
        TemplateView.as_view(template_name="nautobot_chatops_atsu/home.html"),
        name="home",
    ),
    path(
        "docs/",
        TemplateView.as_view(template_name="nautobot_chatops_atsu/docs/index.html"),
        name="docs",
    ),
    # path("settings/", views.PluginSettingsView.as_view(), name="settings"),
]
