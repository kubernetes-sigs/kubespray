import gitlab
import argparse
import os
import sys
from datetime import timedelta, datetime, timezone


from pprint import pprint

parser = argparse.ArgumentParser(
    description='Cleanup old branches in a GitLab project')
parser.add_argument('--api', default='https://gitlab.com/',
    help='URL of GitLab API, defaults to gitlab.com')
parser.add_argument('--age', type=int, default=30,
    help='Delete branches older than this many days')
parser.add_argument('--prefix', default='pr-',
    help='Cleanup only branches with names matching this prefix')
parser.add_argument('--dry-run', action='store_true',
    help='Do not delete anything')
parser.add_argument('project',
    help='Path of the GitLab project')

args = parser.parse_args()
limit = datetime.now(timezone.utc) - timedelta(days=args.age)

if os.getenv('GITLAB_API_TOKEN', '') == '':
    print("Environment variable GITLAB_API_TOKEN is required.")
    sys.exit(2)

gl = gitlab.Gitlab(args.api, private_token=os.getenv('GITLAB_API_TOKEN'))
gl.auth()

p = gl.projects.get(args.project)
for b in p.branches.list(all=True):
    date = datetime.fromisoformat(b.commit['created_at'])
    if date < limit and not b.protected and not b.default and b.name.startswith(args.prefix):
        print("Deleting branch %s from %s ..." %
            (b.name, date.date().isoformat()))
        if not args.dry_run:
            b.delete()
