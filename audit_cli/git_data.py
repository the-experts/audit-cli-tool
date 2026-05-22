import os
import subprocess
from collections import Counter, defaultdict
from datetime import datetime
from typing import Dict, List, Optional, Tuple


def _decode(data: bytes) -> str:
    """Decode git output: try UTF-8 first, fall back to Latin-1.

    Latin-1 maps all 256 byte values 1-to-1 to U+0000–U+00FF so it never
    fails and correctly recovers Western-European characters (ë, é, ü, …)
    that were written in CP1252 / Latin-1 by older git clients on Windows.
    """
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("latin-1")


def _dedup_authors(commits: List[Dict]) -> List[Dict]:
    """
    Resolve commits from the same person committed under different display names.
    Groups by normalised email, then picks the most-frequently-used name per email
    as the canonical identity.
    """
    email_names: Dict[str, Counter] = defaultdict(Counter)
    for c in commits:
        email_names[c["email"].lower()][c["name"]] += 1

    canonical: Dict[str, str] = {
        email: names.most_common(1)[0][0]
        for email, names in email_names.items()
    }
    for c in commits:
        c["name"] = canonical[c["email"].lower()]
    return commits


def fetch_git_log(repo_path: str = ".", since: Optional[str] = None) -> List[Dict]:
    sep = "\x1f"
    cmd = [
        "git",
        "-c", "i18n.logOutputEncoding=UTF-8",
        "-c", "core.quotepath=false",
        "-C", repo_path,
        "log",
        f"--format=%aI{sep}%aE{sep}%aN",
    ]
    if since:
        cmd += [f"--since={since}"]

    result = subprocess.run(cmd, capture_output=True)
    output = _decode(result.stdout)
    if result.returncode != 0:
        raise RuntimeError(_decode(result.stderr).strip() or "git log failed — is this a git repository?")

    repo_name = os.path.basename(os.path.abspath(repo_path))
    commits = []
    for line in output.splitlines():
        parts = line.split(sep)
        if len(parts) != 3:
            continue
        date_str, email, name = parts
        try:
            dt = datetime.fromisoformat(date_str.strip())
        except ValueError:
            continue
        commits.append({
            "date": dt.strftime("%Y-%m-%d"),
            "hour": dt.hour,
            "weekday": dt.weekday(),
            "email": email.strip(),
            "name": name.strip() or email.strip(),
            "repo": repo_name,
        })
    return _dedup_authors(commits)


def fetch_multiple_repos(repo_paths: List[str], since: Optional[str] = None) -> Tuple[List[Dict], List[str]]:
    all_commits = []
    errors = []
    for path in repo_paths:
        try:
            all_commits.extend(fetch_git_log(path, since))
        except RuntimeError as exc:
            errors.append(f"{path}: {exc}")
    if errors and not all_commits:
        raise RuntimeError("\n".join(errors))
    all_commits.sort(key=lambda c: c["date"])
    # Re-run dedup across all repos so the same person using different emails
    # in different repos is still unified if they share an email anywhere.
    _dedup_authors(all_commits)
    return all_commits, errors
