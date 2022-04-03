import json
from turtle import pd
import requests
from requests.auth import HTTPBasicAuth
import click
import csv
from datetime import datetime
import itertools
from tqdm import tqdm

from calcifer.services.github import get_all_repos, get_contributors_for_repo, get_commits_for_repo, get_commits_for_repo_with_tag, get_commit_with_sha


def print_iterator(it):
    for x in it:
        print(x, end=' ')
    print('') 

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
def main_contributors(github_user, github_token, github_org, out_file_path, n_contrib):
    repos = get_all_repos(github_org, github_user, github_token)
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
def first_contribution(github_user, github_token, github_org, out_file_path):
    repos = get_all_repos(github_org, github_user, github_token)
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
def audit_releases(github_user, github_token, github_org, out_file_path):
    repos = get_all_repos(github_org, github_user, github_token)
    print(f'Found {len(repos)} repositories')
    print(f'Retrieving now all releases of this year...')
    commits = [c for c in map(lambda x: get_commits_with_tag(x, github_user, github_token, 'release-2021'), tqdm(repos))]
    write_commits_on_file([c for commits_per_repo in commits for c in commits_per_repo], out_file_path)

@click.group()
def cli():
    pass

cli.add_command(main_contributors)
cli.add_command(first_contribution)
cli.add_command(audit_releases)
