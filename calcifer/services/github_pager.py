import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime
import json
from calcifer.services.rest_pager import RestPager
from pydantic import HttpUrl


class GithubPager(RestPager):

    page_param: str = 'page'
    max_results_param: str = 'per_page'

    def update_params(self, query_params: dict) -> None:
        curr_page_params = query_params.get(self.page_param, -1)
        if curr_page_params > -1:
            query_params[self.page_param] += 1
        else:
         query_params.update({
            self.max_results_param: self.page_size,
            self.page_param: 0
        })

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