import os
import re
import sys
import json
import argparse
import requests


# Do not commit any prints if the script doesn't exit with error code
# Otherwise it will be part of the PR body

github_api_url = 'https://api.github.com/graphql'
gh_token = os.getenv('GH_TOKEN')

def get_commits(tag, release, number_of_commits=5):
    owner = release['owner']
    repo = release['repo']
    repo_url = f'https://github.com/{owner}/{repo}'
    
    query = """
    {
        repository(owner: "%s", name: "%s") {
            ref(qualifiedName: "refs/tags/%s") {
                target {
                    ... on Tag {
                        target {
                            ... on Commit {
                                history(first: %s) {
                                    edges {
                                        node {
                                            oid
                                            message
                                            url
                                        }
                                    }
                                }
                            }
                        }
                    }
                    ... on Commit {
                        # In case the tag directly points to a commit
                        history(first: %s) {
                            edges {
                                node {
                                    oid
                                    message
                                    url
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    """ % (owner, repo, tag, number_of_commits, number_of_commits)

    headers = {'Authorization': f'Bearer {gh_token}'}
    response = requests.post(github_api_url, json={'query': query}, headers=headers)

    if response.status_code == 200:
        try:
            data = response.json()
            target = data['data']['repository']['ref']['target']

            if 'history' in target:
                commits = target['history']['edges']
            elif 'target' in target and 'history' in target['target']:
                commits = target['target']['history']['edges']
            else:
                # print('No commit history found.')
                return None
            
            pr_commits = '\n<details>\n<summary>Commits</summary>\n\n'
            for commit in commits:
                node = commit['node']
                short_oid = node['oid'][:7]
                commit_message = node['message'].split('\n')[0]
                commit_message = link_pull_requests(commit_message, repo_url)
                commit_url = node['url']
                pr_commits += f'- [`{short_oid}`]({commit_url}) {commit_message}  \n'
            pr_commits += '\n</details>'
            return pr_commits
        except Exception as e:
            # print(f'Error parsing commits: {e}')
            # print(f'data: {response.text}')
            return None
    else:
        # print(f'GraphQL query failed with status code {response.status_code}')
        return None


def replace_match(match, repo_url):
    pr_number = match.group(2)
    return f'{match.group(1)}[# {pr_number}]({repo_url}/pull/{pr_number}){match.group(3)}'

def link_pull_requests(input, repo_url):
    return re.sub(r'(\(?)#(\d+)(\)?)', lambda match: replace_match(match, repo_url), input)

def format_description(description, length=20):
    lines = description.splitlines()
    
    if len(lines) > length:
        first_part = '\n'.join(lines[:length])
        collapsed_part = '\n'.join(lines[length:])
        
        formatted_description = f"""{first_part}

<details>
  <summary>Show more</summary>

{collapsed_part}

</details>
"""
        return formatted_description
    else:
        return description

def main(component):
    try:
        with open('version_diff.json') as f:
            data = json.load(f)
            data = data[component]
    except Exception as e:
        print(f'Error loading version_diff.json or component not found: {e}')
        sys.exit(1)

    release = data['release']
    owner = release['owner']
    repo = release['repo']
    
    if component in ['gvisor_containerd_shim','gvisor_runsc']:
        name = release.get('name')
        release_url = f'https://github.com/google/gvisor/releases/tag/{name}'
        pr_body = f"""
### {name}

**URL**: [Release {name}]({release_url})

        """
        commits = get_commits(name, release)
        if commits:
            pr_body += commits
    else:
        name = release['tagName']
        tag_name = release['tagName']
        published_at = release['publishedAt']
        release_url = release['url']
        description = release['description']
        repo_url = 'https://github.com/%s/%s' % (owner, repo)
        description = link_pull_requests(description, repo_url)
        pr_body = f"""
### {name}

**Tag**: {tag_name}  
**Published at**: {published_at}  
**URL**: [Release {tag_name}]({release_url})

#### Description:
{format_description(description)}
        """
        commits = get_commits(name, release)
        if commits:
            pr_body += commits
    print(pr_body)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Pull Request body generator')
    parser.add_argument('--component', required=True, help='Specify the component to process')
    args = parser.parse_args()
    
    main(args.component)
