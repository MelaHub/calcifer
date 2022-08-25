import click
from calcifer.services.jira_pager import JiraPager
from calcifer.commands.jira import (
    get_issues_for_project,
    get_issues_change_logs,
    get_comments_by_issue,
)
from pydantic import SecretStr, HttpUrl
from pathlib import Path
from calcifer.utils.file_writer import write_to_file

from calcifer.services.github_rest_manager import GithubRestManager
from calcifer.commands.github import (
    Repo,
    RepoProtectionInfo,
    add_protection_to_repo_if_missing,
    get_all_repos,
    get_commits_with_tag,
    get_contributors,
    get_first_contributions_by_author,
    get_first_contributions,
    get_repo_protections_info,
    get_missing_catalog_info,
    get_repo_commit_number,
    get_repos_protections,
    get_top_contributors,
    get_last_commit,
)


@click.command()
@click.option("--github-user", envvar="GITHUB_USER", type=str, required=True)
@click.option("--github-token", envvar="GITHUB_TOKEN", type=str, required=True)
@click.option("--github-org", type=str, required=True)
@click.option("--out-file-path", type=str, required=True)
@click.option("--n-contrib", type=int, default=3)
@click.option("--ignore-repos", "-i", type=str, multiple=True)
def top_contributors(
    github_user: str,
    github_token: SecretStr,
    github_org: str,
    out_file_path: Path,
    n_contrib: int,
    ignore_repos: list[str],
):
    """Retrieves the top n contributors for a github org."""
    github_rest_manager = GithubRestManager(
        user=github_user, token=github_token, url="https://api.github.com/"
    )
    repos = get_all_repos(github_rest_manager, ignore_repos, github_org)
    contributors = get_contributors(github_rest_manager, repos)
    top_contributors = get_top_contributors(contributors, n_contrib)
    write_to_file(out_file_path, top_contributors)


@click.command()
@click.option("--github-user", envvar="GITHUB_USER", type=str, required=True)
@click.option("--github-token", envvar="GITHUB_TOKEN", type=str, required=True)
@click.option("--github-org", type=str, required=True)
@click.option("--out-file-path", type=str, required=True)
@click.option("--ignore-repos", "-i", type=str, multiple=True)
def first_contribution(
    github_user: str,
    github_token: SecretStr,
    github_org: str,
    out_file_path: Path,
    ignore_repos: list[str],
):
    """Retrieves the very first contribution for all repos in an org."""
    github_rest_manager = GithubRestManager(
        user=github_user, token=github_token, url="https://api.github.com/"
    )
    repos = get_all_repos(github_rest_manager, ignore_repos, github_org)
    first_contributions = get_first_contributions(github_rest_manager, repos)
    first_contributions_by_author = get_first_contributions_by_author(
        first_contributions
    )
    write_to_file(out_file_path, first_contributions_by_author)


@click.command()
@click.option("--github-user", envvar="GITHUB_USER", type=str, required=True)
@click.option("--github-token", envvar="GITHUB_TOKEN", type=str, required=True)
@click.option("--github-org", type=str, required=True)
@click.option("--ignore-repos", "-i", type=str, multiple=True)
@click.option("--tag", type=str, required=True)
@click.option("--out-file-path", type=str, required=True)
def commits_with_tag(
    github_user: str,
    github_token: SecretStr,
    github_org: str,
    ignore_repos: list[str],
    tag: str,
    out_file_path: Path,
):
    """Retrieves all commits that matches a specific tag actoss al repositories in an organization and writes them to a csv file."""
    github_rest_manager = GithubRestManager(
        user=github_user, token=github_token, url="https://api.github.com/"
    )
    repos = get_all_repos(github_rest_manager, ignore_repos, github_org)
    commits = get_commits_with_tag(github_rest_manager, repos, tag)
    write_to_file(out_file_path, commits)


def __get_empty_repos(
    github_rest_manager: GithubRestManager, repos: list[Repo]
) -> list[str]:
    commits = get_repo_commit_number(github_rest_manager, repos)
    return [commit["name"] for commit in commits if commit["commits"] == 0]


@click.command()
@click.option("--github-user", envvar="GITHUB_USER", type=str, required=True)
@click.option("--github-token", envvar="GITHUB_TOKEN", type=str, required=True)
@click.option("--github-org", type=str, required=True)
@click.option("--ignore-repos", "-i", type=str, multiple=True)
@click.option("--out-file-path", type=str, required=True)
def empty_repos(
    github_user: str,
    github_token: SecretStr,
    github_org: str,
    ignore_repos: list[str],
    out_file_path: Path,
):
    """Retrieves all repos with no commits and writes them to a csv file."""
    github_rest_manager = GithubRestManager(
        user=github_user, token=github_token, url="https://api.github.com/"
    )
    repos = get_all_repos(github_rest_manager, ignore_repos, github_org)
    empty_repos = __get_empty_repos(github_rest_manager, repos)
    write_to_file(out_file_path, empty_repos)


def __get_repos_not_on_main(repos: list[Repo]) -> list[Repo]:
    return [repo for repo in repos if repo["default_branch"] != "main"]


@click.command()
@click.option("--github-user", envvar="GITHUB_USER", type=str, required=True)
@click.option("--github-token", envvar="GITHUB_TOKEN", type=str, required=True)
@click.option("--github-org", type=str, required=True)
@click.option("--ignore-repos", "-i", type=str, multiple=True)
@click.option("--out-file-path", type=str, required=True)
def repos_not_on_main(
    github_user: str,
    github_token: SecretStr,
    github_org: str,
    ignore_repos: list[str],
    out_file_path: Path,
):
    """Retrieves all repos whose main branch is not called main."""
    github_rest_manager = GithubRestManager(
        user=github_user, token=github_token, url="https://api.github.com/"
    )
    repos = get_all_repos(github_rest_manager, ignore_repos, github_org)
    write_to_file(out_file_path, __get_repos_not_on_main(repos))


@click.command()
@click.option("--github-user", envvar="GITHUB_USER", type=str, required=True)
@click.option("--github-token", envvar="GITHUB_TOKEN", type=str, required=True)
@click.option("--github-org", type=str, required=True)
@click.option("--ignore-repos", "-i", type=str, multiple=True)
@click.option("--out-file-path", type=str, required=True)
def backstage_missing(
    github_user: str,
    github_token: SecretStr,
    github_org: str,
    ignore_repos: list[str],
    out_file_path: Path,
):
    """Retrieves all repos that have no catalog-info.yaml and writes them to a csv file."""
    github_rest_manager = GithubRestManager(
        user=github_user, token=github_token, url="https://api.github.com/"
    )
    repos = get_all_repos(github_rest_manager, ignore_repos, github_org)
    repos = get_missing_catalog_info(github_rest_manager, repos)
    write_to_file(out_file_path, repos)


def __get_repo_protection_info(
    github_rest_manager: GithubRestManager, repos: list[Repo], github_org: str
) -> list[RepoProtectionInfo]:
    repos_protections = get_repos_protections(github_rest_manager, repos, github_org)
    return get_repo_protections_info(repos_protections)


@click.command()
@click.option("--github-user", envvar="GITHUB_USER", type=str, required=True)
@click.option("--github-token", envvar="GITHUB_TOKEN", type=str, required=True)
@click.option("--github-org", type=str, required=True)
@click.option("--out-file-path", type=str, required=True)
@click.option("--ignore-repos", "-i", type=str, multiple=True)
@click.option("--add-protection-if-missing", type=bool, required=True, default=False)
def unprotected_repos(
    github_user: str,
    github_token: SecretStr,
    github_org: str,
    out_file_path: Path,
    ignore_repos: list[str],
    add_protection_if_missing: bool,
):
    """Retrieves all unprotected repos in an organization and writes them to a csv file.

    A protected repo is one that satisfy the following rules:
    * required_pull_request_reviews.dismiss_stale_reviews is True
    * required_pull_request_reviews.required_approving_review_count > 0
    * required_linear_history is True
        * allow_force_pushes is False
        * required_status_checks.strict is True
    * enforce_admins is False
    * restrictions is None
    """
    github_rest_manager = GithubRestManager(
        user=github_user, token=github_token, url="https://api.github.com/"
    )
    repos = get_all_repos(github_rest_manager, ignore_repos, github_org)
    flatten_repos_protections = __get_repo_protection_info(
        github_rest_manager, repos, github_org
    )

    if add_protection_if_missing:
        add_protection_to_repo_if_missing(
            github_rest_manager, flatten_repos_protections, github_org
        )
    write_to_file(out_file_path, flatten_repos_protections)


@click.command()
@click.option("--github-user", envvar="GITHUB_USER", type=str, required=True)
@click.option("--github-token", envvar="GITHUB_TOKEN", type=str, required=True)
@click.option("--github-org", type=str, required=True)
@click.option("--out-file-path", type=str, required=True)
@click.option("--ignore-repos", "-i", type=str, multiple=True)
def repo_last_commit(
    github_user: str,
    github_token: SecretStr,
    github_org: str,
    out_file_path: Path,
    ignore_repos: list[str],
):
    github_rest_manager = GithubRestManager(
        user=github_user, token=github_token, url="https://api.github.com/"
    )
    repos = get_all_repos(github_rest_manager, ignore_repos, github_org)
    last_commits = get_last_commit(github_rest_manager, repos)
    write_to_file(out_file_path, last_commits)


@click.command()
@click.option("--github-user", envvar="GITHUB_USER", type=str, required=True)
@click.option("--github-token", envvar="GITHUB_TOKEN", type=str, required=True)
@click.option("--github-org", type=str, required=True)
@click.option("--out-file-path", type=str, required=True)
@click.option("--ignore-repos", "-i", type=str, multiple=True)
def repos_info(
    github_user: str,
    github_token: SecretStr,
    github_org: str,
    out_file_path: Path,
    ignore_repos: list[str],
):
    github_rest_manager = GithubRestManager(
        user=github_user, token=github_token, url="https://api.github.com/"
    )
    repos = get_all_repos(github_rest_manager, ignore_repos, github_org)
    empty_repos = __get_empty_repos(github_rest_manager, repos)
    repos_not_on_main = {repo["name"]: repo for repo in __get_repos_not_on_main(repos)}
    repos_with_missing_backstage = {
        repo["name"]: repo
        for repo in get_missing_catalog_info(github_rest_manager, repos)
    }
    repos_protection_info = {
        repo["name"]: repo
        for repo in __get_repo_protection_info(github_rest_manager, repos, github_org)
    }
    last_commits = {
        commit["repo"]: commit for commit in get_last_commit(github_rest_manager, repos)
    }

    repos_info = []
    for repo in repos:
        repo_info = {
            "name": repo["name"],
            "is_empty": False,
            "is_on_main": True,
            "is_backstage_missing": False,
        }
        if repo["name"] in empty_repos:
            repo_info["is_empty"] = True
        if repo["name"] in repos_not_on_main:
            repo_info["is_on_main"] = False
        if repo["name"] in repos_with_missing_backstage:
            repo_info["is_backstage_missing"] = True
        repo_info.update(repos_protection_info.get(repo["name"], {}))
        repo_info.update(last_commits.get(repo["name"], {}))
        repos_info.append(repo_info)

    write_to_file(out_file_path, repos_info)


@click.command()
@click.option("--jira-user", envvar="JIRA_USER", type=str, required=True)
@click.option("--jira-api-token", envvar="JIRA_API_TOKEN", type=str, required=True)
@click.option(
    "--jira-url",
    envvar="JIRA_URL",
    type=str,
    required=True,
    default="https://instapartners.atlassian.net",
)
@click.option("--search-for-user", type=str, required=True)
@click.option("--jira-project", type=str, required=True)
@click.option(
    "--since", envvar="SINCE", type=str, required=True, default="startOfYear()"
)
@click.option("--out-file-path", type=str, required=True)
def issues_with_comments_by(
    jira_user: str,
    jira_api_token: SecretStr,
    jira_url: HttpUrl,
    search_for_user: str,
    jira_project: str,
    since: str,
    out_file_path: Path,
):
    jira_pager = JiraPager(user=jira_user, token=jira_api_token, url=jira_url)
    issues = get_issues_for_project(jira_pager, jira_project, since)
    issues_comments = get_comments_by_issue(jira_pager, issues, search_for_user)
    write_to_file(out_file_path, issues_comments)


@click.command()
@click.option("--jira-user", envvar="JIRA_USER", type=str, required=True)
@click.option("--jira-api-token", envvar="JIRA_API_TOKEN", type=str, required=True)
@click.option(
    "--jira-url",
    envvar="JIRA_URL",
    type=str,
    required=True,
    default="https://instapartners.atlassian.net",
)
@click.option("--jira-project", envvar="JIRA_PROJECT", type=str, required=True)
@click.option(
    "--since", envvar="SINCE", type=str, required=True, default="startOfYear()"
)
@click.option("--out-file-path", type=str, required=True)
def issues_change_status_log(
    jira_user: str,
    jira_api_token: SecretStr,
    jira_url: HttpUrl,
    jira_project: str,
    since: str,
    out_file_path: Path,
):
    """This command retrieves the list of all status changes for all issues created from `since` of project `jira_project`."""
    jira_pager = JiraPager(user=jira_user, token=jira_api_token, url=jira_url)
    issues = get_issues_for_project(jira_pager, jira_project, since)
    change_log = get_issues_change_logs(jira_pager, issues)
    write_to_file(out_file_path, change_log)


@click.group()
def cli():
    """
    \b
                                       /
                                     */     ,
                                   /// .      /
                               * ./////*      /
                                *//////////      /
                      /     //  ////////////   *// *
                     ///   /////////////////   .////
                  /.      /////////,//,/////  ./////////
                   ///    ////////,*/,,,/////////////////   /   ,
                   ////   //////*,,,*,,,,////,,,,/////////  *//
                * ,////* //////,,,,,,,,,,///,,,,,,,///////  //
               / *///////////*,,,,,,,,,,.,,,,,,,,,,,/,,///  ///
                 ///////,///,,,,,,.,,,,,..,.,,,,,,,,,,,/////////  ,
                 //////*,,,,,,,,,.....,........,,,,,,,,///,,,,///  /  ,
              /  *////,,,,,,,,,..................,,,,,,,,,,,,,,///  /
             //   ///,,,,,,,,,....................     ,,,,,,,,///
            ////////,,,,,*      *............... .%%    (,,,,,*///    *
            ////////,,,,     %%  %............./         /,,,,///  //
            //////,,,,,*         ..............%         ,,,*////////
            /////,,,,,,,%       (................%    %,,,,,,,,/////
             ////,,,,,,,..................,,,,,,,,,,..,,,,,,,,/////&/.
    """
    pass


# Github commands
cli.add_command(commits_with_tag)
cli.add_command(top_contributors)
cli.add_command(first_contribution)
cli.add_command(unprotected_repos)
cli.add_command(empty_repos)
cli.add_command(repos_not_on_main)
cli.add_command(backstage_missing)
cli.add_command(repos_info)
cli.add_command(repo_last_commit)

# Jira commands
cli.add_command(issues_with_comments_by)
cli.add_command(issues_change_status_log)
