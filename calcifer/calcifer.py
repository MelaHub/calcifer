from distutils.file_util import write_file
import json
from turtle import pd
import requests
from requests.auth import HTTPBasicAuth
import click
import csv
from datetime import datetime
import itertools
from tqdm import tqdm
from os.path import exists
from calcifer.services.jira_pager import JiraPager
from calcifer.utils.json_logger import logger
from calcifer.commands.jira import get_issues_for_project, get_issues_change_logs, get_comments_by_issue
from pydantic import SecretStr, HttpUrl
from pathlib import Path
from calcifer.utils.file_writer import write_to_file

from calcifer.services.github_pager import GithubPager
from calcifer.commands.github import get_repo_protections, get_contributors, get_repos_protections, get_top_contributors, get_all_repos, get_commits_with_tag, get_first_contributions, get_first_contributions_by_author


def write_main_contributors_to_file(contributors_repo, out_file_path):
    def get_key_by_index_or_empty(contributors, index, key):
        return contributors['contributors'][index][key] if len(contributors['contributors']) >= (index + 1) else ''

    contributors_by_repo = [{
        'full_name': r['full_name'],
        'total_commits': r['total_commits'],
        'contributor1': get_key_by_index_or_empty(r, 0, 'login'),
        'contributions1': get_key_by_index_or_empty(r, 0, 'contributions'),
        'contributor2': get_key_by_index_or_empty(r, 1, 'login'),
        'contributions2': get_key_by_index_or_empty(r, 1, 'contributions'),
        'contributor3': get_key_by_index_or_empty(r, 2, 'login'),
        'contributions3': get_key_by_index_or_empty(r, 2, 'contributions')}
         for r in contributors_repo]

    if not len(contributors_by_repo):
        print("No data found")
        return

    with open(out_file_path, 'w') as csvfile: 
        writer = csv.DictWriter(csvfile, fieldnames=contributors_by_repo[0].keys())

        writer.writeheader()
        for contrib in contributors_by_repo:
            writer.writerow(contrib)

    print(f'I\'ve written {len(contributors_by_repo)} to {out_file_path}')
    

@click.command()
@click.option("--github-user", envvar="GITHUB_USER", type=str, required=True)
@click.option("--github-token", envvar="GITHUB_TOKEN", type=str, required=True)
@click.option("--github-org", type=str, required=True)
@click.option("--out-file-path", type=str, required=True)
@click.option("--n-contrib", type=int, default=3)
@click.option("--ignore-repos", "-i", type=str, multiple=True)
def top_contributors(github_user, github_token, github_org, out_file_path, n_contrib, ignore_repos):
    """Retrieves the top n contributors for a github org."""
    github_pager = GithubPager(user=github_user, token=github_token, url=f'https://api.github.com/')
    repos = get_all_repos(github_pager, ignore_repos, github_org)
    contributors = get_contributors(github_pager, repos)
    top_contributors = get_top_contributors(contributors, n_contrib)
    write_to_file(out_file_path, top_contributors)

@click.command()
@click.option("--github-user", envvar="GITHUB_USER", type=str, required=True)
@click.option("--github-token", envvar="GITHUB_TOKEN", type=str, required=True)
@click.option("--github-org", type=str, required=True)
@click.option("--out-file-path", type=str, required=True)
@click.option("--ignore-repos", "-i", type=str, multiple=True)
def first_contribution(github_user: str, github_token: str, github_org: str, out_file_path: Path, ignore_repos: list):
    """Retrieves the very first contribution for all repos in an org."""
    github_pager = GithubPager(user=github_user, token=github_token, url=f'https://api.github.com/')
    repos = get_all_repos(github_pager, ignore_repos, github_org)
    first_contributions = get_first_contributions(github_pager, repos)
    first_contributions_by_author = get_first_contributions_by_author(first_contributions)
    write_to_file(out_file_path, first_contributions_by_author)

@click.command()
@click.option("--github-user", envvar="GITHUB_USER", type=str, required=True)
@click.option("--github-token", envvar="GITHUB_TOKEN", type=str, required=True)
@click.option("--github-org", type=str, required=True)
@click.option("--ignore-repos", "-i", type=str, multiple=True)
@click.option("--tag", type=str, required=True)
@click.option("--out-file-path", type=str, required=True)
def commits_with_tag(github_user: str, github_token: SecretStr, github_org: str, ignore_repos: list, tag: str, out_file_path: Path):
    """Retrieves all commits that matches a specific tag actoss al repositories in an organization and writes them to a csv file."""
    github_pager = GithubPager(user=github_user, token=github_token, url=f'https://api.github.com/')
    repos = get_all_repos(github_pager, ignore_repos, github_org)
    commits = get_commits_with_tag(github_pager, repos, tag)
    write_to_file(out_file_path, commits, ["repo", "tag", "author", "message", "date"])


def write_repos_on_file(repo_details, out_file_path):
    headers = ['name', 'required_status_checks', 'dismiss_stale_review','require_approving_review_count', 'allow_force_pushes', 'require_linear_history', 'is_protected_weird', 'is_protection_missing']
    with open(out_file_path, 'w') as csvfile: 
        writer = csv.DictWriter(csvfile, fieldnames=headers)

        writer.writeheader()
        for repo in repo_details:
            writer.writerow({key: repo[key] for key in repo if key in headers})

    print(f'I\'ve written {len(repo_details)} to {out_file_path}')


@click.command()
@click.option("--github-user", envvar="GITHUB_USER", type=str, required=True)
@click.option("--github-token", envvar="GITHUB_TOKEN", type=str, required=True)
@click.option("--github-org", type=str, required=True)
@click.option("--out-file-path", type=str, required=True)
@click.option("--ignore-repos", "-i", type=str, multiple=True)
def unprotected_repos(github_user: str, github_token: SecretStr, github_org: str, out_file_path: Path, ignore_repos: list):
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
    github_pager = GithubPager(user=github_user, token=github_token, url=f'https://api.github.com/')
    repos = get_all_repos(github_pager, ignore_repos, github_org)
    repos_protections = get_repos_protections(github_pager, repos, github_org)
    flatten_repos_protections = get_repo_protections(repos_protections)
    write_to_file(out_file_path, flatten_repos_protections)
    
    # repos_with_weird_protection = [r for r in repo_protections if not r['is_protected_weird']]
    # unprotected_repos = [repo for repo in repo_protections if repo['is_protection_missing']]
    # print(f'Adding protection to {len(unprotected_repos)}')
    # for i, repo in enumerate(unprotected_repos):
    #     print(f'{i+1}/{len(unprotected_repos)} {repo["name"]}')
    #     add_branch_protection('credimi', repo['name'], github_user, github_token, repo['default_branch'])
    #write_repos_on_file([repo for repo in repos_with_weird_protection], out_file_path)


#TODO: parametrizzare progetto e created date
@click.command()
@click.option("--jira-user", envvar="JIRA_USER", type=str, required=True)
@click.option("--jira-api-token", envvar="JIRA_API_TOKEN", type=str, required=True)
@click.option("--jira-url", envvar="JIRA_URL", type=str, required=True, default='https://instapartners.atlassian.net')
@click.option("--search-for-user", type=str, required=True)
@click.option("--jira-project", type=str, required=True)
@click.option("--since", envvar="SINCE", type=str, required=True, default="startOfYear()")
@click.option("--out-file-path", type=str, required=True)
def issues_with_comments_by(jira_user: str, jira_api_token: SecretStr, jira_url: HttpUrl, search_for_user: str, jira_project: str, since: str, out_file_path: Path):
    jira_pager = JiraPager(
        user=jira_user, 
        token=jira_api_token, 
        url=jira_url)
    issues = get_issues_for_project(jira_pager, jira_project, since)
    issues_comments = get_comments_by_issue(jira_pager, issues, search_for_user)
    write_to_file(out_file_path, issues_comments)


@click.command()
@click.option("--jira-user", envvar="JIRA_USER", type=str, required=True)
@click.option("--jira-api-token", envvar="JIRA_API_TOKEN", type=str, required=True)
@click.option("--jira-url", envvar="JIRA_URL", type=str, required=True, default='https://instapartners.atlassian.net')
@click.option("--jira-project", envvar="JIRA_PROJECT", type=str, required=True)
@click.option("--since", envvar="SINCE", type=str, required=True, default="startOfYear()")
@click.option("--out-file-path", type=str, required=True)
def issues_change_status_log(jira_user: str, jira_api_token: SecretStr, jira_url: HttpUrl, jira_project: str, since: str, out_file_path: Path):
    """This command retrieves the list of all status changes for all issues created from `since` of project `jira_project`."""
    jira_pager = JiraPager(
        user=jira_user, 
        token=jira_api_token, 
        url=jira_url)
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
