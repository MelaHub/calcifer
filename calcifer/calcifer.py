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
from calcifer.services.jira import JiraPager
from calcifer.utils.json_logger import logger
from calcifer.commands.jira import get_issues_for_project, get_issues_change_logs

from calcifer.services.github import add_branch_protection, get_branch_protection, get_all_repos, get_contributors_for_repo, get_commits_for_repo, get_commits_for_repo_with_tag, get_commit_with_sha


TAG_RELEASE = 'release-2021'


def get_top_contributors_for_repo(repo, github_user, github_token, n_contrib):
    content = get_contributors_for_repo(repo, github_user, github_token)
    return {
        'full_name': repo['full_name'],
        'total_commits': sum([x['contributions'] for x in content]),
        'contributors': [{'login': c['login'], 'contributions': c['contributions']} for c in content[0:n_contrib]]
    }

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
@click.option("--ignore-repo", "-i", type=str, multiple=True)
def main_contributors(github_user, github_token, github_org, out_file_path, n_contrib, ignore_repo):
    repos = get_all_repos(github_org, github_user, github_token, ignore_repo)
    print(f'Found {len(repos)} repositories')
    print(f'Retrieving now all contributors...')
    contributors_repo = map(lambda x: get_top_contributors_for_repo(x, github_user, github_token, n_contrib), tqdm(repos))
    write_main_contributors_to_file(contributors_repo, out_file_path)

def get_first_contribution_by_repo(repo, github_user, github_token):
    commits = get_commits_for_repo(repo, github_user, github_token)
    date_commits = [{'author': c['commit']['author']['name'], 'date': datetime.strptime(c['commit']['author']['date'], '%Y-%m-%dT%H:%M:%SZ')} for c in commits]        
    return {
        author: {
            'date': min(commit['date'] for commit in commits),
            'repo': repo['name']
        }
        for author, commits in itertools.groupby(date_commits, lambda x: x['author'])}

def get_commits_with_tag(repo, github_user, github_token, tag):
    commits_with_tag = get_commits_for_repo_with_tag(repo, github_user, github_token, tag)
    commits_with_tag_details = []
    for commit in commits_with_tag:
        commit_details = get_commit_with_sha(repo, github_user, github_token, commit['commit']['sha'])
        commits_with_tag_details.append(
            {
                'repo': repo['name'],
                'tag': commit['name'],
                'author': commit_details['commit']['author']['name'],
                'message': commit_details['commit']['message'].replace('\n', '; '),
                'date': commit_details['commit']['author']['date']
            }
        )
    return commits_with_tag_details

def write_commits_on_file(commit_details, out_file_path):
    with open(out_file_path, 'w') as csvfile: 
        writer = csv.DictWriter(csvfile, fieldnames=commit_details[0].keys())

        writer.writeheader()
        for commit in commit_details:
            writer.writerow(commit)

    print(f'I\'ve written {len(commit_details)} to {out_file_path}')

def write_first_contribution_to_file(first_contributions, out_file_path):
    def get_key_by_index_or_empty(contributors, index, key):
        return contributors['contributors'][index][key] if len(contributors['contributors']) >= (index + 1) else ''

    first_contributions_flat = [{
        'author': author,
        'date': first_contributions[author]['date'],
        'repo_name': first_contributions[author]['repo']}
         for author in first_contributions]

    if not len(first_contributions_flat):
        print("No data found")
        return

    with open(out_file_path, 'w') as csvfile: 
        writer = csv.DictWriter(csvfile, fieldnames=first_contributions_flat[0].keys())

        writer.writeheader()
        for contrib in first_contributions_flat:
            writer.writerow(contrib)

    print(f'I\'ve written {len(first_contributions_flat)} to {out_file_path}')

@click.command()
@click.option("--github-user", envvar="GITHUB_USER", type=str, required=True)
@click.option("--github-token", envvar="GITHUB_TOKEN", type=str, required=True)
@click.option("--github-org", type=str, required=True)
@click.option("--out-file-path", type=str, required=True)
@click.option("--ignore-repo", "-i", type=str, multiple=True)
def first_contribution(github_user, github_token, github_org, out_file_path, ignore_repo):
    repos = get_all_repos(github_org, github_user, github_token, ignore_repo)
    print(f'Found {len(repos)} repositories')
    print(f'Retrieving now all contributors...')
    first_contributions = {}
    contributions_in_repo = map(lambda x: get_first_contribution_by_repo(x, github_user, github_token), tqdm(repos))
    for contribution in contributions_in_repo:
        for author in contribution:
            if first_contributions.setdefault(author, {'date': datetime.now(), 'repo': contribution[author]['repo']})['date'] > contribution[author]['date']:
                first_contributions[author] = contribution[author]
    write_first_contribution_to_file(first_contributions, out_file_path)

@click.command()
@click.option("--github-user", envvar="GITHUB_USER", type=str, required=True)
@click.option("--github-token", envvar="GITHUB_TOKEN", type=str, required=True)
@click.option("--github-org", type=str, required=True)
@click.option("--out-file-path", type=str, required=True)
@click.option("--ignore-repo", "-i", type=str, multiple=True)
def audit_releases(github_user, github_token, github_org, out_file_path, ignore_repo):
    repos = get_all_repos(github_org, github_user, github_token, ignore_repo)
    print(f'Found {len(repos)} repositories')
    print(f'Retrieving now all releases of this year...')
    commits = [c for c in map(lambda x: get_commits_with_tag(x, github_user, github_token, TAG_RELEASE), tqdm(repos))]
    write_commits_on_file([c for commits_per_repo in commits for c in commits_per_repo], out_file_path)

def get_repo_protections(repo, github_user, github_token):
    default_branch = repo['default_branch']
    protection = get_branch_protection('credimi', repo['name'], github_user, github_token, default_branch)
    required_status_check = protection.get('required_status_checks', {}).get('strict', False)
    dismiss_stale_review = protection.get('required_pull_request_reviews', {}).get('dismiss_stale_reviews', False)
    require_approving_review_count = protection.get('required_pull_request_reviews', {}).get('required_approving_review_count', 0)
    allow_force_pushes = protection.get('allow_force_pushes', {}).get('enabled', True)
    require_linear_history = protection.get('required_linear_history', {}).get('enabled', False)
    
    repo.update({
        'required_status_checks': required_status_check,
        'dismiss_stale_review': dismiss_stale_review,
        'require_approving_review_count': require_approving_review_count,
        'allow_force_pushes': allow_force_pushes,
        'require_linear_history': require_linear_history,
        'is_protection_missing': not bool(protection),
        'is_protected_weird': require_linear_history and required_status_check and dismiss_stale_review and require_approving_review_count > 0 and not allow_force_pushes
    }
    )
    return repo

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
@click.option("--ignore-repo", "-i", type=str, multiple=True)
def unprotected_repos(github_user, github_token, github_org, out_file_path, ignore_repo):
    repos = get_all_repos(github_org, github_user, github_token, ignore_repo)
    print(f'Found {len(repos)} repositories')
    print(f'Checking whether the main branch is protected')
    repo_protections = [r for r in map(lambda x: get_repo_protections(x, github_user, github_token), tqdm(repos))]
    repos_with_weird_protection = [r for r in repo_protections if not r['is_protected_weird']]
    # unprotected_repos = [repo for repo in repo_protections if repo['is_protection_missing']]
    # print(f'Adding protection to {len(unprotected_repos)}')
    # for i, repo in enumerate(unprotected_repos):
    #     print(f'{i+1}/{len(unprotected_repos)} {repo["name"]}')
    #     add_branch_protection('credimi', repo['name'], github_user, github_token, repo['default_branch'])
    write_repos_on_file([repo for repo in repos_with_weird_protection], out_file_path)


#TODO: parametrizzare progetto e created date
@click.command()
@click.option("--jira-user", envvar="JIRA_USER", type=str, required=True)
@click.option("--jira-api-token", envvar="JIRA_API_TOKEN", type=str, required=True)
@click.option("--jira-url", envvar="JIRA_URL", type=str, required=True, default='https://instapartners.atlassian.net')
@click.option("--search-for-user", type=str, required=True)
def issues_with_comments_by(jira_user, jira_api_token, jira_url, search_for_user):
    issues_cache = './issues_cache.json'
    if exists(issues_cache):
        with open(issues_cache, 'r') as f:
            issues = json.load(f)  
    else:
        issues = get_all_pages(
            f'{jira_url}/rest/api/3/search', 
            {'jql': 'project="Product support" AND createdDate > startOfYear()'}, 
            'issues',
            jira_user, 
            jira_api_token)
        with open(issues_cache, 'w') as f:
            json.dump(issues, f)

    comments_cache = './comments_by.json'
    if exists(comments_cache):
        with open(comments_cache, 'r') as f:
            issues_with_comments_by = json.load(f)  
    else:
        issues_with_comments_by = [comment for comment in map(
            lambda x: get_comments_by_issue(x, jira_url, jira_user, jira_api_token, search_for_user), tqdm(issues)) if comment]
        with open(comments_cache, 'w') as f:
            json.dump(issues_with_comments_by, f)

    with open('comments.csv', 'w') as f:
        f.write('issue,created\n')
        for issue in issues_with_comments_by:
            f.write(f'{issue[0]},{issue[1]}\n')

def get_comments_by_issue(issue, jira_url, jira_user, jira_api_token, search_for_user):
    comments = get_all_pages(
        f'{jira_url}/rest/api/3/issue/{issue["key"]}/comment', {}, 'comments', jira_user, jira_api_token)
    for comment in comments:
        if comment['author']['displayName'] == search_for_user:
            return [issue['key'], issue['fields']['created']]
    return None

@click.command()
@click.option("--jira-user", envvar="JIRA_USER", type=str, required=True)
@click.option("--jira-api-token", envvar="JIRA_API_TOKEN", type=str, required=True)
@click.option("--jira-url", envvar="JIRA_URL", type=str, required=True, default='https://instapartners.atlassian.net')
@click.option("--jira-project", envvar="JIRA_PROJECT", type=str, required=True)
@click.option("--since", envvar="SINCE", type=str, required=True, default="startOfYear()")
def issues_change_status_log(jira_user: str, jira_api_token: str, jira_url: str, jira_project: str, since: str):
    jira_pager = JiraPager(
        user=jira_user, 
        token=jira_api_token, 
        url=jira_url)
    issues = get_issues_for_project(jira_pager, jira_project, since)
    get_issues_change_logs(jira_pager, issues)
    

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

cli.add_command(main_contributors)
cli.add_command(first_contribution)
cli.add_command(audit_releases)
cli.add_command(unprotected_repos)

cli.add_command(issues_with_comments_by)
cli.add_command(issues_change_status_log)
