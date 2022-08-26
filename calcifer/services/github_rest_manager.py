import requests
from requests.auth import HTTPBasicAuth
from typing import Optional
from calcifer.services.rest_pager import DEFAULT_PAGE_SIZE, QueryParams, RestPager
from pydantic import SecretStr, HttpUrl


class GithubQueryParam(QueryParams):
    page: int
    per_page: int
    sha: Optional[str]


def get_default_github_query_param() -> GithubQueryParam:
    return GithubQueryParam(page=1, per_page=DEFAULT_PAGE_SIZE)


class GithubRestManager(RestPager[GithubQueryParam]):
    def __init__(self, url: HttpUrl, user: str, token: SecretStr) -> None:
        self.url = url
        self.auth = HTTPBasicAuth(user, token.get_secret_value())

    def update_params(
        self, query_params: GithubQueryParam, last_results: list[dict]
    ) -> GithubQueryParam:
        new_params = query_params.copy()
        new_params["page"] += 1
        return new_params

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

    def get_file(
        self,
        github_org: str,
        github_repo_name: str,
        file_name: str,
    ) -> Optional[dict]:
        response = requests.get(
            f"https://api.github.com/repos/{github_org}/{github_repo_name}/contents/{file_name}",
            auth=self.auth,
        )
        if response.status_code == 404:
            return None
        return response.content.decode("utf-8")
