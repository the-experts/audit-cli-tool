from typing import Any, Callable, Dict, List, Optional

from .sonarqube import SonarQubeClient

ALL_METRICS = [
    "bugs",
    "vulnerabilities",
    "code_smells",
    "security_hotspots",
    "coverage",
    "duplicated_lines_density",
    "ncloc",
    "sqale_rating",
    "reliability_rating",
    "security_rating",
    "sqale_index",
    "reliability_remediation_effort",
    "security_remediation_effort",
    "blocker_violations",
    "critical_violations",
    "major_violations",
    "minor_violations",
    "info_violations",
    "ncloc_language_distribution",
]

# Metrics stored as raw strings instead of floats
_STRING_METRICS = {"ncloc_language_distribution"}

ISSUE_TYPES = ["BUG", "VULNERABILITY", "CODE_SMELL"]
SEVERITIES = ["BLOCKER", "CRITICAL", "MAJOR", "MINOR", "INFO"]


def _f(v: Any) -> Optional[float]:
    try:
        return float(v) if v is not None else None
    except (ValueError, TypeError):
        return None


def fetch_projects_data(
    client: SonarQubeClient,
    project_keys: Optional[List[str]] = None,
    prefix: Optional[str] = None,
    progress: Optional[Callable[[str], None]] = None,
) -> List[Dict[str, Any]]:
    if progress:
        progress("Fetching project list...")
    all_projects = client.get_projects()
    if project_keys:
        all_projects = [p for p in all_projects if p["key"] in project_keys]
    elif prefix:
        all_projects = [p for p in all_projects if p["key"].startswith(prefix)]

    result = []
    for proj in all_projects:
        key, name = proj["key"], proj["name"]
        if progress:
            progress(f"Fetching metrics for {name}...")
        try:
            measures = client.get_measures(key, ALL_METRICS)
            qg = client.get_quality_gate_status(key)
            row: Dict[str, Any] = {"key": key, "name": name, "qg_status": qg}
            for metric in ALL_METRICS:
                raw = measures.get(metric)
                row[metric] = raw if metric in _STRING_METRICS else _f(raw)
            result.append(row)
        except Exception as exc:
            result.append({"key": key, "name": name, "qg_status": "ERROR", "_error": str(exc)})

    return result


def build_issues_from_projects(projects: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Derive issue counts from per-project metrics (avoids deprecated types filter in SQ 10.x)."""
    return {
        "by_type": {
            "BUG": int(sum(p.get("bugs") or 0 for p in projects)),
            "VULNERABILITY": int(sum(p.get("vulnerabilities") or 0 for p in projects)),
            "CODE_SMELL": int(sum(p.get("code_smells") or 0 for p in projects)),
        },
        "by_severity": {
            "BLOCKER": int(sum(p.get("blocker_violations") or 0 for p in projects)),
            "CRITICAL": int(sum(p.get("critical_violations") or 0 for p in projects)),
            "MAJOR": int(sum(p.get("major_violations") or 0 for p in projects)),
            "MINOR": int(sum(p.get("minor_violations") or 0 for p in projects)),
            "INFO": int(sum(p.get("info_violations") or 0 for p in projects)),
        },
    }


def fetch_security_data(
    client: SonarQubeClient,
    component_keys: Optional[str] = None,
) -> Dict[str, Any]:
    vuln_data = client.get_issues(
        facets="owaspTop10,severities",
        component_keys=component_keys,
        types="VULNERABILITY",
    )

    owasp: Dict[str, int] = {}
    sev_counts: Dict[str, int] = {}
    for facet in vuln_data.get("facets", []):
        if facet["property"] == "owaspTop10":
            owasp = {v["val"]: v["count"] for v in facet["values"] if v["count"] > 0}
        elif facet["property"] == "severities":
            sev_counts = {v["val"]: v["count"] for v in facet["values"] if v["count"] > 0}

    try:
        to_review = client.get_hotspots(
            project_key=component_keys,
            status="TO_REVIEW",
        ).get("paging", {}).get("total", 0)
        reviewed = client.get_hotspots(
            project_key=component_keys,
            status="REVIEWED",
        ).get("paging", {}).get("total", 0)
    except Exception:
        to_review, reviewed = 0, 0

    return {
        "owasp": owasp,
        "vuln_by_severity": sev_counts,
        "hotspots_to_review": to_review,
        "hotspots_reviewed": reviewed,
    }


def fetch_trend(
    client: SonarQubeClient,
    project_key: str,
    metrics: List[str],
    from_date: Optional[str] = None,
) -> Dict[str, List]:
    return client.get_history(project_key, metrics, from_date)
