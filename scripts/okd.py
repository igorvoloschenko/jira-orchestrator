from action import Result
import requests
import json
from urllib.parse import urljoin
from logging import Logger


MAP_BUSINESS_FROM_JIRA = {
    "имя1": "name1",
    "имя2": "name2",
    "имя3": "name3",
}

# базовая функция по работе с квотой
def _quota(mode: str, logger: Logger, **data: dict) -> Result:

    environment = data.get("environment")

    if isinstance(environment, str):
        environment = environment.lower()
    else:
        return Result(message="no environment specified", status=False)

    if not (environment in ["test", "prod"]):
        return Result(
            message="environment is not included in the list ['test', 'prod']", 
            status=False
            )
    
    resource_manager_api_urls = {
    "test": data.get("resource_manager_api_url_test"),
    "prod": data.get("resource_manager_api_url_prod")
    }

    url = urljoin(resource_manager_api_urls[environment], "/v1/resourcequotas")

    namespace = data.get("ns")
    cpu_core = data.get("cpu")
    ram_MiB = data.get("ram")

    if not (cpu_core or ram_MiB):
        return Result(message="no data on cpu and ram", status=False)

    hard = {}

    if cpu_core:
        hard["limits.cpu"] = f"{int(cpu_core)}"

    if ram_MiB:
        hard["limits.memory"] = f"{int(ram_MiB)}Mi"
    
    body = {
        "metadata": {
            "namespace": namespace
            },
        "spec": {
            "hard": hard
            }
        }

    body_json = json.dumps(body)

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    logger.info(f"request: url: {url}, data: {body}, headers: {headers}, mode: {mode}")

    if mode == "create":
        resp = requests.post(url=url, data=body_json, headers=headers)
    elif mode == "update":
        resp = requests.put(url=url, data=body_json, headers=headers)
    else:
        Result(
            message="the argument \"mode\" in the function quota is specified incorrectly", 
            status=False
            )
    
    if resp.status_code != 200:
        return Result(message=f"status_code: {resp.status_code}", status=False)
    
    return Result(status=True)

# Функция по созданию квоты
def create_quota(logger: Logger, **data: dict) -> Result:
    return _quota(mode="create", logger=logger, **data)


# Функция по изменению квоты
def update_quota(logger: Logger, **data: dict) -> Result:
    return _quota(mode="update", logger=logger, **data)

# Функция по созданию проекта в кластере OKD
def create_project(logger: Logger, **data: dict) -> Result:
    environment = data.get("environment")

    if isinstance(environment, str):
        environment = environment.lower()
    else:
        return Result(message="no environment specified", status=False)

    if not (environment in ["test", "prod"]):
        return Result(
            message="environment is not included in the list ['test', 'prod']", 
            status=False
            )

    ci_prepare_svc_api_urls = {
        "test": data.get("ci_prepare_svc_api_url_test"),
        "prod": data.get("ci_prepare_svc_api_url_prod")
        }

    url = urljoin(ci_prepare_svc_api_urls[environment], "/v1/project?mode=simple")

    project_name = data.get("projectname")
    team_name = data.get("teamname")
    team_email = data.get("teamemail")
    namespace = data.get("ns")
    jira_business = data.get("business")
    business = MAP_BUSINESS_FROM_JIRA.get(jira_business)
    jwt_token = data.get("jwt_token")

    body = {
        "namespace": { 
            "name": namespace,
            "annotations": {
                "business.unit": business,
                "project.name": project_name,
                "team.email": team_email,
                "team.name": team_name
            }
        }
    }

    body_json = json.dumps(body)

    logger.info(f"request for create project: (url: {url}, data: {body})")

    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    resp = requests.post(url=url, data=body_json, headers=headers)

    if resp.status_code != 200:
        return Result(message=f"status_code: {resp.status_code}", status=False)

    logger.info(f"request for create project success: (url: {url}, data: {body})")

    cpu_core = data.get("cpu")
    ram_MiB = data.get("ram")

    if not (cpu_core or ram_MiB):
        return Result(status=True)
    
    return create_quota(logger=logger, **data)