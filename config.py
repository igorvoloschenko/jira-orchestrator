import yaml
import os
from glob import glob

from utils import data_fill
from secret import Secret


class Loader(yaml.SafeLoader):

    def __init__(self, stream):

        self._root = os.path.split(stream.name)[0]

        super(Loader, self).__init__(stream)

    def include(self, node):

        include_data = None

        for file in glob(self.construct_scalar(node)):
            filename = os.path.join(self._root, file)

            with open(filename, 'r') as f:
                data = yaml.load(f, Loader)
                if isinstance(data, dict):
                    if include_data:
                        include_data.update(data)
                    else:
                        include_data = data
                
                if isinstance(data, list):
                    if include_data:
                        include_data += data
                    else:
                        include_data = data
        return include_data

Loader.add_constructor('!include', Loader.include)


def Get(path) -> dict:
    """
    Reading configuration from file 
    """
    with open(path) as f:
        return yaml.load(f, Loader)

def SecretFill(data: dict, secret_provider: Secret) -> dict:
    secrets: dict =  secret_provider.Read()
    data_fill(data, secrets)
    return data

def Validate(cfg):
    """
    Validate configuration file
    """

    from schema import Schema, Optional, Or

    conf_schema = Schema({
        Optional('logging'): dict,

        Optional('number_of_try'): int,
        Optional('try_label_prefix'): str,

        'secret': dict,

        'jira': {
            'url': str,
            'auth': {
                'type': str,
                'secret': str
            }
        },

        'tasks': Or([
            {
                'name': str,
                'search': {'JQL': str},
                'map_variables_issue_fields': {str: Or(str, [str])},
                'actions': {
                    int: {
                        'type': str,
                        'desc': str,
                        Optional('variables'): dict,
                        'data': dict,
                        Optional('map_variables_json_fields'): dict
                    }
                },
                'transition_id_success': str,
                'transition_id_problem': str,
                'comment_success': str,
                'comment_problem': str,
                'assignee_problem': str,
                'labels_success': list,
                'labels_problem': list
            }
        ], None),
    })

    conf_schema.validate(cfg)

    return True