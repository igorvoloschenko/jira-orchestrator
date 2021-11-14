
from typing import List, Tuple
from urllib.parse import urljoin, quote
import requests
import json
from requests.models import Response

from utils import getVars


API_PATH = "/rest/api/2/"
ASSIGNEE_STATUS_CODE_SUCCESS = 204
COMMENT_STATUS_CODE_SUCCESS = 201
TRANSITION_STATUS_CODE_SUCCESS = 204
ISSUE_STATUS_CODE_SUCCESS = 204


def FormationJQL(data: dict) -> str:
    """
    Forming part of the JQL request
    """
    jql = data.get("JQL")
    return "jql=" + quote(jql)

class Issue:
    def __init__(self, data, jira=None):
        self.data = data
        self.id = data.get('id')
        self.jira = jira

    def baseRequest(self, method, url, data: str, status_code_success) -> Tuple[str, bool]:
        try:
            resp: Response = self.jira.Request(
                method=method, 
                url=url, 
                data=data
                )

            status_code = resp.status_code

            if status_code != status_code_success:
                return f"responce status code: {status_code}; message: {resp.text}", False
            return f"responce status code: {status_code}", True

        except Exception as e:
            return e, False

    def GetVars(self, mapVarField: dict) -> dict:
        return getVars(self.data, mapVarField)

    def SetAssignee(self, assignee: str) -> Tuple[str, bool]:
        data = {
            "name": assignee
        }

        url=f"issue/{self.id}/assignee"
        
        return self.baseRequest(
            method="PUT", 
            url=url, 
            data=json.dumps(data), 
            status_code_success=ASSIGNEE_STATUS_CODE_SUCCESS
            )

    def SetComment(self, comment: str) -> Tuple[str, bool]:
        data = {
            "body": comment
        }

        url=f"issue/{self.id}/comment"

        return self.baseRequest(
            method="POST", 
            url=url, 
            data=json.dumps(data), 
            status_code_success=COMMENT_STATUS_CODE_SUCCESS
            )

    def AddLabels(self, labels: List):
        add_labels: List = [{"add": label} for label in labels]
        data = {
            "update":{
                "labels":add_labels
                }
        }

        url=f"issue/{self.id}"

        return self.baseRequest(
            method="PUT", 
            url=url, 
            data=json.dumps(data), 
            status_code_success=ISSUE_STATUS_CODE_SUCCESS
            )

    def SetTransition(self, transition_id: str) -> Tuple[str, bool]:
        data = {
            "transition": {
                "id": transition_id
            }
        }

        url=f"issue/{self.id}/transitions"
        
        return self.baseRequest(
            method="POST", 
            url=url, 
            data=json.dumps(data), 
            status_code_success=TRANSITION_STATUS_CODE_SUCCESS
            )


class Jira:
    def __init__(self, url, auth_type="", auth_secret="", proxies=None):
        self.url = url
        self.auth_type = auth_type
        self.auth_secret = auth_secret
        self.proxies = proxies

    def IsAvailable(self):
        """
        Проверяет доступность Jira. Если сервис недоступен - выбрасывается исключение
        """
        self.Request(method="HEAD")
    
    def Request(self, **req_data) -> Response:
        api_url = urljoin(self.url, API_PATH)
        req_data["url"] = urljoin(api_url, req_data.get('url'))

        req = requests.Request(**req_data)

        s = requests.Session()

        prepared = s.prepare_request(req)
        prepared.headers['Authorization'] = f"{self.auth_type} {self.auth_secret}"
        prepared.headers['Content-Type'] = "application/json"

        return s.send(prepared, proxies=self.proxies)

    def GetIssues(self, jql) -> Tuple[List[Issue], str]:
        issues = []
        startAt = 0
        while True:
            try:
                param = "?" + jql + f"&startAt={startAt}&maxResults=50"
                resp: Response = self.Request(method="GET", url="search" + param)
                
                if resp.status_code != 200:
                    raise Exception(resp.text)

                # data: {"startAt":<startAt>,"maxResults":50,"total":<issues_total>,"issues":[...]}
                data = resp.json()
                
                for issue in data["issues"]:
                    issues.append(Issue(issue, jira=self))

                startAt = len(issues)
                page_total = data["total"]                
                if startAt >= page_total:
                    return issues, ""
            except Exception as e:
                return [], e


def NewClient(cfg):
    url = cfg.get('url')
    auth = cfg.get('auth')
    if not isinstance(auth, dict):
        auth = {}

    return Jira(
        url=url, 
        auth_type=auth.get("type"), 
        auth_secret=auth.get("secret"))