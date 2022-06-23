import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime
import json


REPO_PAGE_SIZE = 100


def _get_all_pages(url, query_params, github_user, github_token, stop_if=lambda x: False, page_size=REPO_PAGE_SIZE, max_results=None):
    page_size = page_size if max_results is None or max_results > page_size else max_results
    results = []
    query_params.update({
        'per_page': page_size,
        'page': 0
    })
    while query_params['page'] is not None and (max_results is None or max_results is not None and len(results) < max_results):
        query_params_str = '&'.join([f'{k}={query_params[k]}' for k in query_params])
        response = requests.get(f'{url}?{query_params_str}', auth = HTTPBasicAuth(github_user, github_token))
        if response.status_code in (404, 409):
            return []
        elif response.status_code != 200:
            raise Exception("Something went wrong while calling the github api")
        curr_res = json.loads(response.content)
        if len(curr_res):
            query_params['page'] += 1
            valid_results = [res for res in curr_res if not stop_if(res)]
            results += valid_results
            if len(valid_results) < len(curr_res):
                break
        else:
            query_params['page'] = None
    return results


def get_contributors_for_repo(repo, github_user, github_token):
    response = requests.get(repo['contributors_url'].replace('{/collaborator}', ''), auth = HTTPBasicAuth(github_user, github_token))
    content = []
    if response.status_code != 200 and response.status_code != 204:
        raise Exception(f"Something went wrong while fetching details of repo {repo}")
    elif response.status_code == 200:
        content = json.loads(response.content)
    return content

def get_commits_for_repo_with_tag(repo, github_user, github_token, tag):
    all_commits = _get_all_pages(repo['git_tags_url'].replace('{/sha}', '').replace('/git/tags', '/tags'), {}, github_user, github_token)
    release_commits = [commit for commit in all_commits if tag in commit['name']]
    return release_commits

def get_commit_with_sha(repo, github_user, github_token, sha):
    commit_url = repo['commits_url'].replace('{/sha}', f"/{sha}")
    response = requests.get(commit_url, auth = HTTPBasicAuth(github_user, github_token))
    if response.status_code != 200:
        raise Exception(f"Something went wrong while fetching {commit_url}")
    return json.loads(response.content)

def get_commits_for_repo(repo, github_user, github_token):
    stop_if = lambda x: datetime.strptime(x['commit']['author']['date'], '%Y-%m-%dT%H:%M:%SZ') < datetime(2021, 1, 1)
    main_response = _get_all_pages(repo['commits_url'].replace('{/sha}', ''), {'sha': 'main'}, github_user, github_token, stop_if=stop_if)
    master_response = _get_all_pages(repo['commits_url'].replace('{/sha}', ''), {'sha': 'master'}, github_user, github_token, stop_if = stop_if)
    return main_response + master_response

def get_all_repos(github_org, github_user, github_token, ignore_repos=None):
    print(f'Retrieving all {github_org} repos - hold on...')
    if not ignore_repos:
        ignore_repos = []
    repos = _get_all_pages(f'https://api.github.com/orgs/{github_org}/repos', {}, github_user, github_token)
    return [r for r in repos if r['name'] not in ignore_repos]