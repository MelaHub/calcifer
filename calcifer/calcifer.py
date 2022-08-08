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
    add_protection_to_repo_if_missing,
    get_repo_protections,
    get_contributors,
    get_repos_protections,
    get_top_contributors,
    get_all_repos,
    get_commits_with_tag,
    get_first_contributions,
    get_first_contributions_by_author,
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
    out_file_path: str,
    n_contrib: int,
    ignore_repos: list,
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
    ignore_repos: list,
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
    ignore_repos: list,
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
    ignore_repos: list,
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
    repos_protections = get_repos_protections(github_rest_manager, repos, github_org)
    flatten_repos_protections = get_repo_protections(repos_protections)

    if add_protection_if_missing:
        add_protection_to_repo_if_missing(
            github_rest_manager, flatten_repos_protections, github_org
        )

    write_to_file(out_file_path, flatten_repos_protections)


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

# Jira commands
cli.add_command(issues_with_comments_by)
cli.add_command(issues_change_status_log)
