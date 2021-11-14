## Jira-orchestrator

### Описание
Скрипт для автоматической обработки задач из Jira.

Скрипт опрашивает Jira на наличие задач которые попадают под условие указанное в блоке конфигурации `search`. Полученные данные с задачи передаются для выполнения следующих шагов - действий(action).

При выполнении всех действий, описанных в блоке `actions` - задача считается обработанной и она переводится в статус указанный в ключе `transition_id_success`. Если возникли проблемы при выполнении - в статус `transition_id_problem`.

Также в процессе выполнения или ошибки, можно назначать исполнителя и отправлять комментарий в задачу Jira, используя ключи:
- `comment_success` - комментарий к задаче при удачном выполнении
- `comment_problem` - комментарий к задаче при проблемах в выполнении
- `assignee_problem` - участник на которого будет назначена задача при проблемах

Поддерживаются два типа действий при обработке задачи:
1. Request - делается http-запрос.

2. Script - выполнение скрипта. 


#### Request
В Request задается тип запроса и другие данные: тело, заголовок и т.п.

Пример Request:
```
actions:
...
      type: request

      data:
        method: "POST"
        url: "http://ci-prepare-svc.local/v1/project"
        headers:
          Accept: application/json
          Content-Type: application/json
        body:
          namespace:
            annotations:
              business.unit: "{{ business }}"
              project.name: "{{ projectname }}"
              team.email: "{{ teamemail }}"
              team.name: "{{ teamname }}"
            name: "{{ namespace }}"
        
        session: {}
        
        code_success: 200
```
Здесь выполняется `POST` запрос на url `http://ci-prepare-svc.local/v1/project` в теле запроса передается json:
```
POST http://ci-prepare-svc.local/v1/project
{
"namespace": {
    "annotations": {
        "business.unit": "<имя_колонны>",
        "project.name": "<projectname>",
        "team.email": "<teamemail>",
        "team.name": "<teamname>",
        }
    "name": "<namespace>"
    }
}
```
если код ответа равен code_success(в данном случае 200), то действие считается выполненным

#### Script
Скрипты пишутся отдельно и складываются в папку `scripts`. Входная точка скрипта пишется на Python. Скрипт оформляется как файл `<namescript>.py` с функциями. Имя скрипта и функции в дальнейшем прописывается в конфигурации, блок `actions`, ключ `module_name` и `func_name`. 

Пример Script:
```
actions:
...
  type: script

  data:
      variables: 
          base_url: https://gitlab.example/
          token: "{{ secret.gitlab_token }}"
      module_name: gitlab
      func_name: create_user_gitlab
      desc: create user in gitlab 
```
Здесь запускается функция create_user_gitlab из файла scripts/gitlab.py. Этой функции передается набор аргументов сформированных в блоке конфигурации map_variables_issue_fields и в variables.
Скрипт должен вернуть ответ в виде json:
`{'status': bool, 'message': string, ...}`
Если status = true и нет ошибок при выполнении скрипта, то это действие считается выполненным.

Если требуется запускать внешние утилиты или скрипты написанные на других языках программирования, то это делается из python функции.

#### Использование секретных данных
Для заполнения конфигурации секретными данными(пароль, токен и т.п.) используется провайдер-секретов. Провайдер формирует секретные переменные которые можно будет использовать в конфигурации.

Пример:
```
...
## блок для подключения к jira
jira:
  url: "https://jira.example/"
  auth:
    type: Bearer
    secret: "{{ secret.jira_token }}"
...
```


### Разворачивание и запуск

Проект устанавливается через helm-chart, папка helm

Запуск осуществляется через CronJob в кластере Kubernetes/Openshift. Частота запуска настраивается в файле helm/values.yaml