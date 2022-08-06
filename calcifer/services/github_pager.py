import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime
import json
from calcifer.services.rest_pager import RestPager
from pydantic import HttpUrl


class GithubPager(RestPager):

    page_param: str = 'page'
    max_results_param: str = 'per_page'

    def update_params(self, query_params: dict):
        curr_page_params = query_params.get(self.page_param, -1)
        if curr_page_params > -1:
            query_params[self.page_param] += 1
        else:
         query_params.update({
            self.max_results_param: self.page_size,
            self.page_param: 0
        })

def get_contributors_for_repo(repo, github_user, github_token):
    response = requests.get(repo['contributors_url'].replace('{/collaborator}', ''), auth = HTTPBasicAuth(github_user, github_token))
    content = []
    if response.status_code != 200 and response.status_code != 204:
        raise Exception(f"Something went wrong while fetching details of repo {repo}")
    elif response.status_code == 200:
        content = json.loads(response.content)
    return content

def get_commits_for_repo(repo, github_user, github_token):
    pass
#     stop_if = lambda x: datetime.strptime(x['commit']['author']['date'], '%Y-%m-%dT%H:%M:%SZ') < datetime(2021, 1, 1)
#     main_response = _get_all_pages(repo['commits_url'].replace('{/sha}', ''), {'sha': 'main'}, github_user, github_token, stop_if=stop_if)
#     master_response = _get_all_pages(repo['commits_url'].replace('{/sha}', ''), {'sha': 'master'}, github_user, github_token, stop_if = stop_if)
#     return main_response + master_response

def get_branch_protection(github_org, github_repo_name, github_user, github_token, main_branch):
    response = requests.get(f'https://api.github.com/repos/{github_org}/{github_repo_name}/branches/{main_branch}/protection', auth = HTTPBasicAuth(github_user, github_token))
    if response.status_code == 404:
        return {}
    return json.loads(response.content)

DEFAULT_PROTECTION = {
	"required_pull_request_reviews": {
		"dismiss_stale_reviews": True,
		"required_approving_review_count": 1
	},
	"required_linear_history": True,
	"allow_force_pushes": False,
	"required_status_checks": {
		"strict": True,
		"contexts": []
	},
	"enforce_admins": False,
	"restrictions": None
}

def add_branch_protection(github_org, github_repo_name, github_user, github_token, main_branch):
    response = requests.put(f'https://api.github.com/repos/{github_org}/{github_repo_name}/branches/{main_branch}/protection', json=DEFAULT_PROTECTION, auth = HTTPBasicAuth(github_user, github_token))
    if response.status_code != 200:
        import curlify
        print(curlify.to_curl(response.request))
        raise Exception(f"Something went wrong while adding branch protection to {github_repo_name}")