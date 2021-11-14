from typing import List
from jira import NewClient, Jira, FormationJQL
import logging

import action


def GetTryNumber(issue_labels: List[str], tryLabelPrefix: str) -> int:
    """
    Возвращает максимальное число в списке issue_labels у меток с префиксом tryLabelPrefix
    >>> issue_labels = ["try-2", "try-1", "try-3"]
    >>> tryLabelPrefix = "try-"
    >>> GetTryNumber(issue_labels, tryLabelPrefix)
    3
    """
    tryNumbers = []
    for label in issue_labels:
        if label.startswith(tryLabelPrefix):
            try:
                tryNumbers.append(int(label[len(tryLabelPrefix):]))
            except ValueError:
                continue
    if tryNumbers:
        return max(tryNumbers)
    return 0

def TaskRunner(jira: Jira, task: dict, numberOfTry=3, tryLabelPrefix="try-"):
    """
    Function for processing task
    """
    task_name: str = task.get('name')
    map_variables_issue_fields: dict = task.get('map_variables_issue_fields')
    actions: dict = task.get('actions')
    transition_id_success: str = task.get('transition_id_success')
    comment_success: str = task.get('comment_success')
    transition_id_problem: str = task.get('transition_id_problem')
    comment_problem: str = task.get('comment_problem')
    assignee_problem: str = task.get('assignee_problem')
    labels_success: str = task.get('labels_success')
    labels_problem: str = task.get('labels_problem')

    log = logging.getLogger(name=task_name)
    
    jql: str = FormationJQL(task['search'])

    log.info(f"search issues in jira")

    issues, err = jira.GetIssues(jql) # list object jira.Issue class

    number_tasks = len(issues)

    if number_tasks == 0:
        if err != "":
            log.error(f"search issues in jira\n{err}")
        else:
            log.info("issue list is empty")
        return

    log.info(f"number of found issues: {number_tasks}")
    
    log.info("start processing issues")

    for issue in issues:
        issue_key: str = issue.data.get('key')
        logIssue = logging.getLogger(name=f"{task_name}; {issue_key}")

        fields = issue.data.get('fields')
        issue_labels: List[str] = fields.get('labels')
        if not issue_labels:
            issue_labels = []
        logIssue.info(f"labels for actions: {issue_labels}")
        try_number_current = GetTryNumber(issue_labels, tryLabelPrefix)
        logIssue.info(f"try number current: {try_number_current}")

        logIssue.info(f"get data fields in issue")
        vars: dict = issue.GetVars(map_variables_issue_fields)
        logIssue.info(f"vars for actions: {vars}")

        logIssue.info(f"start processing actions")
        try:
            result = action.Processing(vars, actions, logger=logIssue)
            message = result.message
            ok = result.status

        except Exception as e:
            message, ok = str(e), False

        if ok:
            assignee = ""
            comment = comment_success
            transition_id = transition_id_success
            labels = labels_success
        else: 
            logIssue.error(f"execution problems: {message}")
            if try_number_current < numberOfTry:
                labels = [tryLabelPrefix+str(try_number_current+1)]
                assignee = ""
                comment = ""
                transition_id = ""
            else:
                comment = comment_problem
                transition_id = transition_id_problem
                labels = labels_problem
                assignee = assignee_problem

        if assignee:
            msg, ok = issue.SetAssignee(assignee_problem)
            log_msg = (f"set issue assignee {assignee_problem}: {msg}")
            if not ok:
                logIssue.error(log_msg)
            else:
                logIssue.info(log_msg)

        if comment:
            msg, ok = issue.SetComment(comment)
            log_msg = (f"set issue comment {comment}: {msg}")
            if not ok:
                logIssue.error(log_msg)
            else:
                logIssue.info(log_msg)

        if labels:
            msg, ok = issue.AddLabels(labels)
            log_msg = f"add labels {labels} in issue: {msg}"
            if not ok:
                logIssue.error(log_msg)
            else:
                logIssue.info(log_msg)

        if transition_id:
            msg, ok = issue.SetTransition(transition_id)
            log_msg = f"set transition id {transition_id}: {msg}"
            if not ok:
                logIssue.error(log_msg)
            else:
                logIssue.info(log_msg)
        

def Run(cfg):
    # Получение списка задач из конфигурации
    tasks = cfg.get('tasks')
    if not tasks:
        raise Exception("empty list of tasks in configuration")

    jira: Jira = NewClient(cfg.get('jira'))
    
    # Проверяет доступность Jira. Если сервис недоступен - выбрасывается исключение
    jira.IsAvailable()

    try_cfg = {
        "numberOfTry": cfg.get('number_of_try'),
        "tryLabelPrefix": cfg.get('try_label_prefix'),
    }
    try_cfg = {k: v for k, v in try_cfg.items() if v}

    logging.info("Start processing tasks")
    for task in tasks:
        TaskRunner(jira, task, **try_cfg)

    logging.info("Tasks processing finish.")
    