from action import Result
import gitlab
from logging import Logger, info
from transliter import Transliter

AccessLevelMap = {
    "reporter": gitlab.REPORTER_ACCESS,
    "developer": gitlab.DEVELOPER_ACCESS,
    "maintainer": gitlab.MAINTAINER_ACCESS
}

def _parseJiraObjIDs(jira_object_ids: list) -> list:
    """
    ["211 (CMDB-8672)", ...] -> ["211", ...]
    """
    return [item.split()[0] for item in jira_object_ids]


def gitlab_access(logger: Logger, **data) -> Result:
    # получение URL и токена с последующим созданием объекта gitlab
    url = data.get('gitlab_url')
    token = data.get('gitlab_token')
    gl = gitlab.Gitlab(url=url, private_token=token)

    # получение роли пользователя
    role = data.get('role')
    if role in AccessLevelMap:
        access_level = AccessLevelMap[role]
    else:
        return Result.New(message=f"получение роли пользователя: {role}", status=False)

    # получение списка пользователей из задачи
    users = data.get('users')
    
    # получение типа объекта: группа/проект
    type_object_id = data.get('type_object_id')

    if type_object_id == '18611': # если группа
        # получение списка id группы
        jira_object_ids = data.get('id_groups')

    elif type_object_id == '18610': # если проект
        # получение списка id проекта
        jira_object_ids = data.get('id_projects')    

    # jira_object_ids: ["211 (CMDB-8672)", ...] -> obj_ids: ["211", ...]
    obj_ids = _parseJiraObjIDs(jira_object_ids)
    logger.info(f"jira object id: {obj_ids=}")

    for id in obj_ids:
        if type_object_id == '18611': # если группа
            # получение группы
            logger.info(f"get group id {id}")
            obj = gl.groups.get(id)

        elif type_object_id == '18610': # если проект
            # получение проекта
            logger.info(f"get project id {id}")
            obj = gl.projects.get(id)

        else:
            raise Exception(f"id object of unknown type: {type_object_id}")

        for user in users:
            userEmail = user.get("emailAddress")
            if not userEmail:
                raise Exception(f"unspecified email for user {user['name']}")

            gl_users = gl.users.list(search=userEmail)
            gl_user = None

            # проверка на наличие пользователя в GitLab
            if not gl_users:
                # создание пользователя в GitLab
                displayName = user.get('displayName')

                # displayName = 'Иванов Иван Иванович' -> revers_name = 'Иван Иванов'
                revers_name = " ".join(displayName.split()[1::-1])

                # translit
                tr = Transliter()
                # revers_name = 'Иван Иванов' -> name_translit='Ivan Ivanov'
                name = tr.translate(revers_name)

                email = user.get('emailAddress')
                username = user.get('name')

                logger.info(f"{username=}, {email=}, {name=}")
                gl_user = gl.users.create(
                    {
                        'email': email,
                        'reset_password': True,
                        'username': username,
                        'name': name,
                    }
                )
            else:
                gl_user = gl_users[0]

            if gl_user:
                logger.info(f"gitlab user id: {gl_user.id}")
                try:
                    member = obj.members.get(gl_user.id)
                except gitlab.exceptions.GitlabGetError:
                    member = None

                logger.info(f"{member=}")
            else:
                raise Exception(f"GitLab user {gl_user}")

            # проверка на присутствие пользователя в группе/проекте
            if not member:
                # добавление пользователя в группу/проект
                try:
                    
                    member = obj.members.create(
                        {
                            'user_id': gl_user.id, 
                            'access_level': access_level,
                            }
                    )
                except gitlab.exceptions.GitlabCreateError as e:
                    logger.warning(f"members create group/project {obj.id}, user id {gl_user.id}: {e}")
                    continue

            else:
                if member.access_level != access_level:
                    member.access_level = access_level
                    member.save()

    return Result.New(status=True)