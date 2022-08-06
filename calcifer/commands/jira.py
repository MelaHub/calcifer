from functools import cache
from calcifer.services.jira_pager import JiraPager
from calcifer.utils.json_logger import logger
import json
from os.path import exists
from calcifer.utils.cache import cache_to_file


from tqdm import tqdm

@cache_to_file(file_prefix='issues_for_project')
def get_issues_for_project(jira_pager: JiraPager, jira_project: str, since: str):
    jql_query = f'project={jira_project} AND createdDate > {since}'
    logger.info(f"Retrieving Jira issues with jql {jql_query}")
    issues = jira_pager.get_all_pages(
            f'/rest/api/3/search', 
            {'jql': jql_query}, 
            'issues')
    return issues

@cache_to_file(file_prefix='issues_change_status_log')
def get_issues_change_logs(jira_pager: JiraPager, issues: json):
    change_logs = []

    for i in tqdm(issues):
        change_log = jira_pager.get_all_pages(
            f'/rest/api/3/issue/{i["key"]}/changelog',
            {}, 
            'values',
            show_progress=False)
        for log in change_log:
            for field in log['items']:
                if field['field'] == 'status':
                    assignee = i['fields']['assignee']['displayName'] if i['fields']['assignee'] else None
                    change_logs.append([i['key'], assignee, log['created'], field['fromString'], field['toString']])
    return change_logs