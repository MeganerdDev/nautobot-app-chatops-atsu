# Nautobot Chatops Atsu


<p align="center">
  <img src="https://raw.githubusercontent.com/meganerddev/nautobot-app-chatops-atsu/main/docs/images/icon-nautobot-chatops-atsu.png" class="logo" height="200px">
  <br>
  An <a href="https://networktocode.com/nautobot-apps/">App</a> for <a href="https://nautobot.com/">Nautobot</a>.
</p>


## Overview
This is a Nautobot App to show creating ChatOps commands/sub-commands.
I did one twist on this repo from the cookiecutter template, I added a mock dispatcher so I don't need mattermost/slack/teams for this demo purposes.


## How to create your own ChatOps App, similar to this
This repo was created from the Nautobot ChatOps Cookiecutter, which provided the template for the example. I crafted this to show a specific command you might implement (get-prefixes).
1. Clone down https://github.com/nautobot/cookiecutter-nautobot-app locally, change directory to that
2. Create the virtual environment with poetry `poetry shell && poetry install && cookiecutter nautobot-app-chatops/`
3. Fill prompts from cookiecutter
4. Your template is now generated! You might init a git repo in that directory now (like this one!)
5. You may have some other things left to do for the "App" that my template is not providing? eg a proper `urls.py` file


## Requirements to use this repo
- \>\=Python3.9, Poetry, Docker


## How to use this repo
1. Clone down the repo, change directory to that
2. Create the virtual environment with poetry `poetry shell && poetry install`
3. You may need to create or modify `./development/creds.env` file (modify from `./development/creds.example.env`)
4. Use invoke task to build the Docker container `invoke build`
5. Use invoke task to start the Docker container `invoke start` (allow time for the container to provision database on first spin up)
6. You should be able to access Nautobot UI at http://127.0.0.1:8080 and login with the admin from creds.env
7. Under the Admin Panel of Nautobot, provide the 'test' user account permissions to the endpoints. (IPAM, Status, and User objects in this case)
8. Create some test Prefixes, since there are none in the fresh database instance
9. Drop in to one of the Docker containers with a shell, then enter the Nautobot shell (Django shell)
```bash
$ docker ps
CONTAINER ID   IMAGE                                         COMMAND                  CREATED          STATUS                    PORTS                                       NAMES
73146e79b6c3   nautobot-chatops-atsu/nautobot:2.3.1-py3.11   "sh -c 'watchmedo au…"   29 minutes ago   Up 28 minutes (healthy)   8080/tcp                                    nautobot-chatops-atsu-worker-1
7fafe2d2431c   nautobot-chatops-atsu/nautobot:2.3.1-py3.11   "sh -c 'watchmedo au…"   29 minutes ago   Up 28 minutes             8080/tcp                                    nautobot-chatops-atsu-beat-1
8e704908ffdd   nautobot-chatops-atsu/nautobot:2.3.1-py3.11   "/docker-entrypoint.…"   29 minutes ago   Up 28 minutes (healthy)   0.0.0.0:8080->8080/tcp, :::8080->8080/tcp   nautobot-chatops-atsu-nautobot-1
e3119c10dc7d   postgres:13-alpine                            "docker-entrypoint.s…"   29 minutes ago   Up 29 minutes (healthy)   5432/tcp                                    nautobot-chatops-atsu-db-1
8f345b642243   redis:6-alpine                                "docker-entrypoint.s…"   29 minutes ago   Up 29 minutes             6379/tcp                                    nautobot-chatops-atsu-redis-1
$ docker exec -it nautobot-chatops-atsu-nautobot-1 /bin/bash
root@8e704908ffdd:/source# nautobot-server shell_plus
```
10. Copy the example script from `./development/django-shell-demo.txt` or from below
```python3
from pkg_resources import UnknownExtra
from django.contrib.auth import get_user_model
from nautobot.ipam.models import Prefix
from nautobot.extras.models import Status
from nautobot_chatops.workers import handle_subcommands
from nautobot_chatops_atsu import worker
from nautobot_chatops_atsu import helpers

status_qs = Status.objects.get_for_model(Prefix)
active_status = status_qs.get(name="Active")
params = ["status", f"{active_status.pk}"]

User = get_user_model()
test_user, created = User.objects.get_or_create(
    username="test", # NOTE: test user needs permissions for this object
    defaults={
        "email": "test@example.com",
    }
)

context = {
    "user": test_user,
    "user_name": test_user.username,
    "user_id": test_user.pk,
    "platform_name": "mock",
    "platform_color": "000000",
    "command_prefix": "/",
}

captured = {}
class Capture_Dispatcher(helpers.Mock_Dispatcher):
    def __init__(self, context: dict = {}):
        super().__init__(context=context)
        captured["disp"] = self

try:
    result = handle_subcommands(
        "atsu",
        "get-prefixes",
        params,
        Capture_Dispatcher,
        context,
    )
except UnknownExtra as exc:
    # suppress pkg_resources warning for mock demo
    pass
except Exception as exc:
    # suppress anything else for mock demo
    pass

print(f"Result: {result}")
# Result: succeeded

for md in captured["disp"].sent_markdowns:
    print(md)
Command /atsu get-prefixes received with filter type 'status' and filter value '0c83cd98-e084-4e17-afd1-2c0c75e60e06'
# **Showing prefixes filtered by 'status'**
# | Prefix | Status | Role | Namespace |
# | --- | --- | --- | --- |
# | 10.0.0.0/8 | Active |  | Global |
# | 192.168.1.0/24 | Active |  | Global |
```


## How to create your own ChatOps App, similar to this
This repo was created from the Nautobot ChatOps Cookiecutter, which provided the template for the example. I crafted this to show a specific command you might implement (get-prefixes).
1. Clone down https://github.com/nautobot/cookiecutter-nautobot-app locally
2. `poetry shell && poetry install && cookiecutter nautobot-app-chatops/`
3. Fill prompts from cookiecutter
4. Your template is now generated! You might init a git repo in that directory now (like this one!)

