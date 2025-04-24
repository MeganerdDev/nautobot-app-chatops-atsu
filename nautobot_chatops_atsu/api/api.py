import os
from pathlib import Path
import sys
import yaml

from pynautobot import api


class API:
    def __init__(self, url: str, token: str):
        self.url = url
        self.token = token
        self.api = api(url=url, token=token)
        self.endpoints = {}
        self.load_endpoints()

    def load_endpoints(self):
        self.endpoints = {}
        directory = Path("api/endpoints")
        for yaml_definition in directory.glob("*.y*ml"):
            if "template.yaml" == yaml_definition.name:
                continue
            data = {}
            with open(yaml_definition, "r") as file:
                data = yaml.safe_load(file)
            self.endpoints[yaml_definition.name] = data

    def test_api_token(self) -> bool:
        return True

    def action(self, name):
        endpoint = self.api
        data = self.endpoints[name]

        for ep in data["endpoint"].split("."):
            endpoint = getattr(endpoint, ep)

        result = None
        if data["action"].upper() == "GET":
            if "filters" in data:
                print(
                    f"querying endpoint for {data['endpoint']} objects with filters {data['filters']}"
                )
                result = endpoint.filter(**data["filters"])
            else:
                print(f"querying endpoint {data['endpoint']} for all objects")
                result = endpoint.all()

            if not result:
                print("No results found")
                sys.exit()

            print(f"result: {result}")

        elif data["action"].upper() == "POST":
            result = endpoint.create(data["data"])
            print(result)

        elif data["action"].upper() == "PUT":
            if "filters" not in data:
                print("filters required for PUT action")
            else:
                obj = endpoint.filter(**data["filters"])[0]
                obj.update(data["data"])
                print(f"updated {obj}")

        elif data["action"].upper() == "DELETE":
            if "filters" not in data:
                print("filters required for DELETE action")
            else:
                obj = endpoint.filter(**data["filters"])[0]
                obj.delete()
                print(f"deleted {obj}")

        else:
            print(f"unsupported api action {data['action']}")

        if result:
            return result
