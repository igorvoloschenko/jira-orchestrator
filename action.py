from logging import Logger
from typing import List
import requests
from utils import data_fill, getVars


class Result:
    """
    Result: класс для передачи результата выполненного действия
    """
    def __init__(self, message="", status=False, data=None):
        self.message = message
        self.status = status
        self.data = data

    def SetMessage(self, message):
        self.message = message

    def __repr__(self) -> str:
        from json import dumps
        return dumps(self.__dict__)

    @staticmethod
    def New(message="", status=False, data=None):
        return Result(message, status, data)


class Action:
    @staticmethod
    def New(action_data, logger: Logger):
        map_actions = {
            "request": Request,
            "script": Script 
        }
        return map_actions[action_data['type']](logger, **action_data['data'])

    def Run(self, vars: dict) -> Result:
        """
        Run метод для запуска действия
        входные данные: словарь с переменными которые формируются из задачи jira
        выходные данные: словарь с полями "message": str, "status": bool
        """
        ...


class Request(Action):
    def __init__(self, logger: Logger, **data: dict):
        self.logger = logger
        code_success = data.pop("code_success")
        if isinstance(code_success, list):
            self.code_success = code_success
        else:
            self.code_success = [code_success]
        
        if "body" in data:
            body = data.pop("body")
            data['data'] = body
        
        self.session = {}
        if "session" in data:
            self.session = data.pop("session")
        
        self.data = data

    def prepare_data(self, vars: dict):
        """
        prepare_data: заполнение шаблона переменными
        """
        data_fill(self.data, vars)
        

    def Run(self, vars: dict) -> Result:
        s = requests.Session()
        
        # Заполнение данных запроса переменными <vars>
        self.prepare_data(vars)

        req = requests.Request(**self.data)
        prepare = req.prepare()
        
        # HTTP запрос
        resp = s.send(prepare, **self.session)
      
        status_code = resp.status_code

        if status_code in self.code_success:
            try:
                resp_data = resp.json()
            except:
                resp_data = {}

            return Result.New(message="", status=True, data=resp_data)

        return Result.New(
            message=f"response status code: {status_code}"
        )


class Script(Action):
    def __init__(self, logger: Logger, module_name: str, func_name: str):
        self.logger = logger
        self.module_name = module_name
        self.func_name = func_name

    def Run(self, vars: dict) -> Result:
        import scripts
        
        try:
            module = getattr(scripts, self.module_name)
            func = getattr(module, self.func_name)
            return func(self.logger, **vars)
                       
        except Exception as e:
            return Result.New(
                message=e,
                status=False
            )


def actionExecute(vars: dict, action_data: dict, logger: Logger) -> Result:
    # обновление/дополнение переменных в vars полученных из variables
    # действует в пределах этого действия
    map_vars = action_data.get("variables")
    if map_vars:
        vars.update(map_vars)

    # формирование объекта action в зависимости от полученных данных в action_data
    action: Action = Action.New(action_data, logger=logger)
    return action.Run(vars)

def Processing(vars: dict, actions: dict, logger: Logger) -> Result:
    if not actions:
        return Result.New(message="empty actions")

    for id_action in sorted(actions.keys()):
        action_data = actions[id_action]
        action_type = action_data["type"]
        action_desc = action_data['desc']

        logger.info(f"start action: type: \"{action_type}\", description: \"{action_desc}\"")
        result = actionExecute(vars.copy(), action_data, logger)

        if not result.status:
            logger.info(f"action execute failed: type: \"{action_type}\", description: \"{action_desc}\"")
            return result
        
        result_data = result.data

        # обновление/дополнение переменных в vars полученных из map_variables_json_fields
        map_variables_json_fields = action_data.get("map_variables_json_fields")
        if isinstance(result_data, dict) and isinstance(map_variables_json_fields, dict):
            moreVars = getVars(result_data, map_variables_json_fields)
            vars.update(moreVars)
    
    return result
