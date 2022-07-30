from calcifer.utils.json_logger import logger
import json
from os.path import exists

from tqdm import tqdm

def get_issues_for_project(jira_pager, jira_project, since):
    issues_cache = './issues_pfm_cache.json'
    jql_query = f'project="{jira_project}" AND createdDate > {since}'
    logger.info(f"Retrieving issues status log with jql {jql_query}")
    if exists(issues_cache):
        with open(issues_cache, 'r') as f:
            issues = json.load(f)  
    else:
        issues = jira_pager.get_all_pages(
            f'/rest/api/3/search', 
            {'jql': jql_query}, 
            'issues')
        with open(issues_cache, 'w') as f:
            json.dump(issues, f)

    return issues

def get_issues_change_logs(jira_pager, issues):
    change_log_cache = './change_status_log'
    if exists(change_log_cache):
        with open(change_log_cache, 'r') as f:
            issues = json.load(f)  
    else:
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

        with open(change_log_cache, 'w') as f:
            json.dump(change_logs, f)