from jinja2 import Template, Undefined
import re


class CustomUndefined(Undefined):
     __slots__ = ()

     def __getattr__(self, _: str):
         return self

     def __str__(self) -> str:
         return f"{{{{ {self._undefined_name} }}}}"


def data_fill(data, vars: dict):
    """
    Заполнение шаблона текстовых полей объекта <data>, переменными из <vars>
    Пример:
    >>> vars = {"ns": "default"}
    >>> data = {"namespace": "{{ ns }}"}
    >>> data_fill(data, vars)
    >>> data
    {"namespace": "default"}
    """

    for item in data:
        if isinstance(data, dict):
            value = data[item]
        elif isinstance(data, list):
            value = item

        if isinstance(value, dict):
            data_fill(value, vars)
        
        if isinstance(value, list):
            data_fill(value, vars)

        if isinstance(value, str):
            tmpl = Template(value, undefined=CustomUndefined)
            render_out: str = tmpl.render(vars)

            if isinstance(data, dict):
                data[item] = render_out
            
            elif isinstance(data, list):
                data[data.index(item)] = render_out
    return


def getValueFromDict(fieldPath: str, data: dict):
    """
    Получение значение из документа <data> по пути <fieldPath>
    Пример: 
      fieldPath = 'key1.key2[0].key3'
      data = {'key1': {'key2': [{'key3': 'value'}]}}
      getValueFromDict(fieldPath, data)
      >>> 'value'
    """
    keys = [int(item) if re.match(r'\d+', item) else item for item in re.findall(r'\w+', fieldPath)]

    value = data.copy()

    for key in keys:
        value = value[key]

    return value

def getVars(data: dict, mapVarField: dict) -> dict:
    vars = {}
    for varName in mapVarField:
        field = mapVarField[varName]
        value = getValueFromDict(field, data)
        vars[varName] = value
    return vars
