import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime
import json
from calcifer.services.rest_pager import RestPager

class GithubPager(RestPager):
    start_at_param: str = 'page',
    max_results_param: str = 'page_size',
    total_param: str = 'total'

    # TODO: this doesn't work for github bcs it does not return the number of items :\

def get_contributors_for_repo(repo, github_user, github_token):
    response = requests.get(repo['contributors_url'].replace('{/collaborator}', ''), auth = HTTPBasicAuth(github_user, github_token))
    content = []
    if response.status_code != 200 and response.status_code != 204:
        raise Exception(f"Something went wrong while fetching details of repo {repo}")
    elif response.status_code == 200:
        content = json.loads(response.content)
    return content

def get_commits_for_repo_with_tag(repo, github_user, github_token, tag):
    github_pager = GithubPager(
        user=github_user, 
        token=github_token, 
        url=repo['git_tags_url'].replace('{/sha}', '').replace('/git/tags', '/tags'))
    all_commits = github_pager.get_all_pages('', {}, github_user, github_token)
    release_commits = [commit for commit in all_commits if tag in commit['name']]
    return release_commits

def get_commit_with_sha(repo, github_user, github_token, sha):
    commit_url = repo['commits_url'].replace('{/sha}', f"/{sha}")
    response = requests.get(commit_url, auth = HTTPBasicAuth(github_user, github_token))
    if response.status_code != 200:
        raise Exception(f"Something went wrong while fetching {commit_url}")
    return json.loads(response.content)

def get_commits_for_repo(repo, github_user, github_token):
    pass
#     stop_if = lambda x: datetime.strptime(x['commit']['author']['date'], '%Y-%m-%dT%H:%M:%SZ') < datetime(2021, 1, 1)
#     main_response = _get_all_pages(repo['commits_url'].replace('{/sha}', ''), {'sha': 'main'}, github_user, github_token, stop_if=stop_if)
#     master_response = _get_all_pages(repo['commits_url'].replace('{/sha}', ''), {'sha': 'master'}, github_user, github_token, stop_if = stop_if)
#     return main_response + master_response

def get_all_repos(github_org, github_user, github_token, ignore_repos=None):
    print(f'Retrieving all {github_org} repos - hold on...')
    if not ignore_repos:
        ignore_repos = []
    github_pager = GithubPager(
        user=github_user, 
        token=github_token, 
        url='https://api.github.com')
    repos = github_pager.get_all_pages(f'/orgs/{github_org}/repos', {}, github_user, github_token)
    return [r for r in repos if r['name'] not in ignore_repos]