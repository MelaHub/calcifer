from functools import cache
from typing import Callable
from calcifer.models.github import (
    Repo,
    FlattenCommit,
    Tag,
    Contributor,
    ContributorWithRepo,
    CommitDetails,
    AuthorContribution,
    RepoProtection,
    RepoProtectionInfo,
    RepoCommits,
)
from calcifer.services.github_rest_manager import (
    GithubRestManager,
    get_default_github_query_param,
)
from calcifer.utils.cache import cache_to_file
from calcifer.utils.json_logger import logger
from tqdm import tqdm
from datetime import datetime
import itertools


@cache_to_file(file_prefix="github_repos")
def get_all_repos(
    github_rest_manager: GithubRestManager, ignore_repos: list[str], github_org: str
) -> list[Repo]:
    print(
        f"Retrieving all not archived repos for org {github_org}, ignoring {ignore_repos}"
    )
    repos = github_rest_manager.get_all_pages(
        f"orgs/{github_org}/repos", get_default_github_query_param(), None
    )
    return [r for r in repos if r["name"] not in ignore_repos and not r["archived"]]


@cache_to_file(file_prefix="github_release_commits")
def get_commits_with_tag(
    github_rest_manager: GithubRestManager, repos: list[Repo], tag: str
) -> list[FlattenCommit]:
    print(f"Retrieving all commits with tag {tag}")
    commits = []
    for repo in tqdm(repos):
        commits += get_repo_commits_with_tag(github_rest_manager, repo, tag)
    return commits


def get_repo_commits_with_tag(
    github_rest_manager: GithubRestManager, repo: Repo, tag: str
) -> list[FlattenCommit]:
    commits_with_tag = get_commits_for_repo_with_tag(github_rest_manager, repo, tag)
    commits_with_tag_details = []
    for commit in commits_with_tag:
        commit_details = get_commit_with_sha(
            github_rest_manager, repo, commit["commit"]["sha"]
        )
        commits_with_tag_details.append(
            FlattenCommit(
                repo=repo["name"],
                tag=commit["name"],
                author=commit_details["commit"]["author"]["name"],
                message=commit_details["commit"]["message"].replace("\n", "; "),
                date=commit_details["commit"]["author"]["date"],
            )
        )
    return commits_with_tag_details


def get_commits_for_repo_with_tag(
    github_rest_manager: GithubRestManager, repo: Repo, tag: str
) -> list[Tag]:
    all_commits = github_rest_manager.get_all_pages(
        repo["git_tags_url"].replace("{/sha}", "").replace("/git/tags", "/tags"),
        get_default_github_query_param(),
        None,
        show_progress=False,
    )
    return [commit for commit in all_commits if tag in commit["name"]]


def get_commit_with_sha(
    github_rest_manager: GithubRestManager, repo: Repo, sha: str
) -> list[CommitDetails]:
    commit_url = repo["commits_url"].replace("{/sha}", f"/{sha}")
    return github_rest_manager.get_all_pages(
        commit_url, get_default_github_query_param(), None, show_progress=False
    )[0]


@cache_to_file(file_prefix="github_first_contribution")
def get_first_contributions(
    github_rest_manager: GithubRestManager, repos: list
) -> list[dict[str, AuthorContribution]]:
    print("Retrieving first contributions")
    contributions = []
    for repo in tqdm(repos):
        contributions_by_repo = get_first_contributions_by_repo(
            github_rest_manager, repo
        )
        if len(contributions_by_repo):
            contributions.append(contributions_by_repo)
    return contributions


@cache_to_file(file_prefix="github_languages")
def get_repos_languages(github_rest_manager: GithubRestManager, repos: list):
    print("Retrieving repo languages")
    repo_languages = {}
    for repo in tqdm(repos):
        languages = get_languages_by_repo(github_rest_manager, repo)
        repo_languages[repo["name"]] = languages
    return repo_languages

def get_languages_by_repo(github_rest_manager: GithubRestManager, repo: dict):
    return github_rest_manager.get_all_pages(
        repo["languages_url"],
        get_default_github_query_param(),
        None,
        show_progress=False,
        stop_if=get_first_page()
    )[0]


def get_first_contributions_by_author(
    contributions: list[dict[str, AuthorContribution]]
) -> list[AuthorContribution]:
    first_contributions = {}
    now = datetime.now().isoformat()
    for contribution in contributions:
        for author in contribution:
            curr_author_contribution = {
                "date": now,
                "repo": contribution[author]["repo"],
            }
            if (
                first_contributions.setdefault(author, curr_author_contribution)["date"]
                > contribution[author]["date"]
            ):
                first_contributions[author] = {
                    "date": contribution[author]["date"],
                    "repo": contribution[author]["repo"],
                }
    return [contrib for contrib in first_contributions.values()]


def get_first_contributions_by_repo(
    github_rest_manager: GithubRestManager, repo: str
) -> dict[str, AuthorContribution]:
    commits = get_all_commits_for_repo(
        github_rest_manager, repo, stop_if=_stop_if_after_2021
    )
    date_commits = [
        {"author": c["commit"]["author"]["name"], "date": c["commit"]["author"]["date"]}
        for c in commits
    ]
    return {
        author: {
            "author": author,
            "date": min(commit["date"] for commit in commits),
            "repo": repo["name"],
        }
        for author, commits in itertools.groupby(date_commits, lambda x: x["author"])
    }


def _stop_if_after_2021(commit: CommitDetails) -> bool:
    return datetime.strptime(
        commit["commit"]["author"]["date"], "%Y-%m-%dT%H:%M:%SZ"
    ) < datetime(2021, 1, 1)


def get_first_page() -> Callable[dict, bool]:
    has_already_been_called_once = False

    def stop_if_after_first_page(page: dict) -> bool:
        nonlocal has_already_been_called_once
        if has_already_been_called_once:
            return True
        has_already_been_called_once = True
        return False

    return stop_if_after_first_page


@cache_to_file(file_prefix="github_first_page_of_commits")
def get_repos_first_page_commits(
    github_rest_manager: GithubRestManager, repos: list[Repo]
) -> list[RepoCommits]:
    commits = []
    for repo in tqdm(repos):
        repo_commits = get_all_commits_for_repo(
            github_rest_manager, repo, stop_if=get_first_page()
        )
        commits += repo_commits
    return commits


def get_last_commit(
    github_rest_manager: GithubRestManager, repos: list[Repo]
) -> list[FlattenCommit]:
    logger.info("Retrieving last commit")
    repo_commits = get_repos_first_page_commits(github_rest_manager, repos)
    last_commits = []
    for _, commits in itertools.groupby(repo_commits, lambda x: x["repo"]):
        last_commits.append(sorted(commits, key=lambda x: x["date"])[-1])
    return last_commits


def get_repo_commit_number(
    github_rest_manager: GithubRestManager, repos: list[Repo]
) -> list[RepoCommits]:
    logger.info("Retrieving number of commits")
    repos_commits = get_repos_first_page_commits(github_rest_manager, repos)
    commits_num = []
    for repo in repos:
        repo_commits = [commit for commit in repos_commits if commit["repo"] == repo["name"]]
        commits_num.append({"name": repo["name"], "commits": len(repo_commits)})
    return commits_num


def get_all_commits_for_repo(
    github_rest_manager: GithubRestManager, repo: Repo, stop_if=None
) -> list[FlattenCommit]:
    query_params_with_sha = get_default_github_query_param()
    query_params_with_sha.update({"sha": repo["default_branch"]})
    commits = github_rest_manager.get_all_pages(
        repo["commits_url"].replace("{/sha}", ""),
        query_params_with_sha,
        None,
        stop_if=stop_if,
        show_progress=False,
    )
    return [
        FlattenCommit(
            repo=repo["name"],
            tag=commit["sha"],
            author=commit["commit"]["author"]["name"],
            message=commit["commit"]["message"].replace("\n", "; "),
            date=commit["commit"]["author"]["date"],
        )
        for commit in commits
    ]


@cache_to_file(file_prefix="github_top_contributions")
def get_contributors(
    github_rest_manager: GithubRestManager, repos: list[Repo]
) -> list[ContributorWithRepo]:
    all_contributors = []
    for repo in tqdm(repos):
        repo_contributors = get_contributors_for_repo(github_rest_manager, repo)
        for contributor in repo_contributors:
            contributor.update({"repo": repo["name"]})
        all_contributors += repo_contributors
    return all_contributors


def get_contributors_for_repo(
    github_rest_manager: GithubRestManager, repo: list[Repo]
) -> list[Contributor]:
    return github_rest_manager.get_all_pages(
        repo["contributors_url"].replace("{/collaborator}", ""),
        get_default_github_query_param(),
        None,
        show_progress=False,
    )


def get_top_contributors(
    contributors: list[ContributorWithRepo], n_contributors: int
) -> dict:
    top_contributors = []
    for repo, contributions in itertools.groupby(contributors, lambda x: x["repo"]):
        contributors = {}
        sorted_contributors = sorted(
            contributions, key=lambda x: x["contributions"], reverse=True
        )[:n_contributors]
        for i in range(0, n_contributors):
            if i < len(sorted_contributors):
                contributors.update(
                    {
                        f"contributor{i + 1}_login": sorted_contributors[i]["login"],
                        f"contributor{i + 1}_contributions": sorted_contributors[i][
                            "contributions"
                        ],
                    }
                )
            else:
                contributors.update(
                    {
                        f"contributor{i + 1}_login": None,
                        f"contributor{i + 1}_contributions": None,
                    }
                )
        contributors.update(
            {
                "repo": sorted_contributors[0]["repo"],
                "total_commits": sum([x["contributions"] for x in sorted_contributors]),
            }
        )
        top_contributors.append(contributors)
    return top_contributors


def get_missing_catalog_info(
    github_rest_manager: GithubRestManager, repos: list[Repo]
) -> list[Repo]:
    missing_catalog_info = []
    for repo in tqdm(repos):
        if github_rest_manager.get_file(
            repo["owner"]["login"],
            repo["name"],
            "catalog-info.yaml",
        ):
            continue
        missing_catalog_info.append(repo)
    return missing_catalog_info


@cache_to_file(file_prefix="github_repo_protections")
def get_repos_protections(
    github_rest_manager: GithubRestManager, repos: list[Repo], github_org: str
) -> list[RepoProtectionInfo]:
    print("Retrieving repo protections")
    protections = []
    for repo in tqdm(repos):
        protections_by_repo = get_protections_by_repo(
            github_rest_manager, repo, github_org
        )
        protections.append(protections_by_repo)
    return protections


def get_protections_by_repo(
    github_rest_manager: GithubRestManager, repo: Repo, github_org: str
) -> list[RepoProtectionInfo]:
    default_branch = repo["default_branch"]
    repo_protection_rules = {
        "repo": repo["name"],
        "visibility": repo["visibility"],
    }
    protections = github_rest_manager.get_all_pages(
        f'repos/{github_org}/{repo["name"]}/branches/{default_branch}/protection',
        get_default_github_query_param(),
        None,
        show_progress=False,
    )
    if len(protections):
        repo_protection_rules.update(protections[0])
    return repo_protection_rules


def get_repo_protections_info(repos: list[RepoProtection]) -> list[RepoProtectionInfo]:
    protections = []
    for repo in repos:
        required_status_check = repo.get("required_status_checks", {}).get(
            "strict", False
        )
        dismiss_stale_review = repo.get("required_pull_request_reviews", {}).get(
            "dismiss_stale_reviews", False
        )
        require_approving_review_count = repo.get(
            "required_pull_request_reviews", {}
        ).get("required_approving_review_count", 0)
        allow_force_pushes = repo.get("allow_force_pushes", {}).get("enabled", True)
        require_linear_history = repo.get("required_linear_history", {}).get(
            "enabled", False
        )
        is_protection_missing = True if not repo.get("url") else False

        protections.append(
            {
                "name": repo["repo"],
                "visibility": repo["visibility"],
                "required_status_checks": required_status_check,
                "dismiss_stale_review": dismiss_stale_review,
                "require_approving_review_count": require_approving_review_count,
                "allow_force_pushes": allow_force_pushes,
                "require_linear_history": require_linear_history,
                "is_protection_missing": is_protection_missing,
            }
        )
    return protections


def add_protection_to_repo_if_missing(
    github_rest_manager: GithubRestManager,
    repo_protections: list[RepoProtectionInfo],
    github_org: str,
) -> None:
    unprotected_repos = [
        repo for repo in repo_protections if repo["is_protection_missing"]
    ]
    logger.info(f"Adding protection to {len(unprotected_repos)}")
    for i, repo in enumerate(unprotected_repos):
        logger.info(
            f'{i+1}/{len(unprotected_repos)} Adding protection to {repo["name"]}'
        )
        try:
            github_rest_manager.add_protections(
                github_org, repo["name"], repo["default_branch"], DEFAULT_PROTECTION
            )
        except Exception as e:
            logger.error(f'Error adding protection to {repo["name"]}: {e}')
            continue


DEFAULT_PROTECTION = {
    "required_pull_request_reviews": {
        "dismiss_stale_reviews": True,
        "required_approving_review_count": 1,
    },
    "required_linear_history": True,
    "allow_force_pushes": False,
    "required_status_checks": {"strict": True, "contexts": []},
    "enforce_admins": False,
    "restrictions": None,
}
