import requests
from requests.auth import HTTPBasicAuth
from calcifer.services.rest_pager import RestPager


class GithubRestManager(RestPager):

    page_param: str = "page"
    max_results_param: str = "per_page"

    def update_params(self, query_params: dict) -> None:
        curr_page_params = query_params.get(self.page_param, -1)
        if curr_page_params > -1:
            query_params[self.page_param] += 1
        else:
            query_params.update(
                {self.max_results_param: self.page_size, self.page_param: 0}
            )

    def add_protections(
        self,
        github_org: str,
        github_repo_name: str,
        main_branch: str,
        protections: dict,
    ) -> None:
        response = requests.put(
            f"{self.url}https://api.github.com/repos/{github_org}/{github_repo_name}/branches/{main_branch}/protection",
            json=protections,
            auth=HTTPBasicAuth(self.user, self.token.get_secret_value()),
        )
        if response.status_code not in (200, 204):
            raise Exception(
                f"Something went wrong while adding branch protection to {github_repo_name}"
            )
