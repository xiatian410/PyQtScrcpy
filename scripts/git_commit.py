#!/usr/bin/env python3
"""Commit with the active GitHub CLI identity, without storing personal details."""
import json
import os
from pathlib import Path
import subprocess
import sys


def github_identity():
    result = subprocess.run(
        ['gh', 'api', '--hostname', 'github.com', 'user'],
        check=True, capture_output=True, text=True, encoding='utf-8',
    )
    account = json.loads(result.stdout)
    login, account_id = account['login'], account['id']
    if not isinstance(login, str) or not login or not isinstance(account_id, int):
        raise ValueError('GitHub returned an invalid account identity')
    return login, f'{account_id}+{login}@users.noreply.github.com'


def commit_environment():
    name, email = github_identity()
    env = os.environ.copy()
    for role in ('AUTHOR', 'COMMITTER'):
        env[f'GIT_{role}_NAME'] = name
        env[f'GIT_{role}_EMAIL'] = email
    return env


def main():
    try:
        env = commit_environment()
    except (OSError, subprocess.CalledProcessError, ValueError, KeyError) as error:
        print(f'Cannot resolve the active GitHub identity: {error}', file=sys.stderr)
        print('Check gh auth status --hostname github.com; no commit was created.', file=sys.stderr)
        return 1
    root = Path(__file__).resolve().parents[1]
    return subprocess.run(['git', 'commit', *sys.argv[1:]], cwd=root, env=env).returncode


if __name__ == '__main__':
    sys.exit(main())
