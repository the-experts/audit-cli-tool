import os
import sys
from typing import Optional

import click
import yaml
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from . import data as dt
from . import git_data
from .charts import save_html
from .charts import (
    coverage_landscape,
    debt_coverage,
    debt_heatmap,
    git_commits,
    health_overview,
    issues_breakdown,
    ownership_map,
    project_matrix,
    radar,
    ratings_distribution,
    remediation as remediation_chart,
    risk_matrix,
    security_dist,
    security_per_project,
    summary_table,
    trend,
    violations,
)
from .sonarqube import SonarQubeClient, SonarQubeError

console = Console()

_URL_HELP = "SonarQube URL  [env: SONAR_URL]"
_TOKEN_HELP = "SonarQube token  [env: SONAR_TOKEN]"


def _client(url: str, token: str) -> SonarQubeClient:
    return SonarQubeClient(url, token)


def _out(output: str, name: str, fmt: str) -> str:
    os.makedirs(output, exist_ok=True)
    return os.path.join(output, f"{name}.{fmt}")


def _emit(sections, path, title):
    """Save sections and print every file path that was written."""
    for p in save_html(sections, path, title):
        console.print(f"[green]✓[/green] Saved → {p}")


def _fetch_projects(client: SonarQubeClient, project: Optional[str], prefix: Optional[str] = None) -> list:
    keys = [project] if project else None
    with Progress(SpinnerColumn(), TextColumn("{task.description}"), console=console) as prog:
        task = prog.add_task("Fetching data…", total=None)
        projects = dt.fetch_projects_data(client, keys, prefix=prefix, progress=lambda msg: prog.update(task, description=msg))
    return projects


def _component_keys(client: SonarQubeClient, project: Optional[str], prefix: Optional[str]) -> Optional[str]:
    if project:
        return project
    if prefix:
        all_projs = client.get_projects()
        keys = [p["key"] for p in all_projs if p["key"].startswith(prefix)]
        return ",".join(keys) if keys else None
    return None


@click.group()
def cli() -> None:
    """SonarQube diagram generator — visualise code quality at a glance."""


# ─── shared options decorator ──────────────────────────────────────────────
def _common(f):
    for dec in reversed([
        click.option("--url", envvar="SONAR_URL", required=True, help=_URL_HELP),
        click.option("--token", envvar="SONAR_TOKEN", required=True, help=_TOKEN_HELP),
        click.option("-o", "--output", default="sonar-reports", show_default=True, help="Output directory"),
        click.option("-f", "--format", "fmt", type=click.Choice(["html", "png"]), default="html", show_default=True),
        click.option("--project", default=None, help="Restrict to a single project key"),
        click.option("--prefix", default=None, help="Restrict to projects whose key starts with this prefix"),
    ]):
        f = dec(f)
    return f


# ─── health ────────────────────────────────────────────────────────────────
@cli.command()
@_common
def health(url, token, output, fmt, project, prefix):
    """Per-project health overview — Quality Gate, bugs, coverage, duplications."""
    client = _client(url, token)
    projects = _fetch_projects(client, project, prefix)
    _emit(health_overview.build(projects), _out(output, "health_overview", fmt), "Per-Project Health Overview")
    _print_health_summary(projects)


def _print_health_summary(projects: list) -> None:
    t = Table(title="Quick Summary", show_lines=True)
    t.add_column("Project", style="cyan", max_width=40)
    t.add_column("QG", justify="center")
    t.add_column("Bugs", justify="right")
    t.add_column("Vulns", justify="right")
    t.add_column("Coverage", justify="right")
    for p in projects:
        qg = p.get("qg_status", "?")
        qg_style = "green" if qg == "OK" else ("red" if qg == "ERROR" else "yellow")
        cov = p.get("coverage")
        cov_str = f"{cov:.1f}%" if cov is not None else "-"
        t.add_row(
            p["name"][:40],
            f"[{qg_style}]{qg}[/{qg_style}]",
            str(int(p.get("bugs") or 0)),
            str(int(p.get("vulnerabilities") or 0)),
            cov_str,
        )
    console.print(t)


# ─── issues ────────────────────────────────────────────────────────────────
@cli.command()
@_common
def issues(url, token, output, fmt, project, prefix):
    """Issues breakdown by type and severity — derived from reliable project metrics."""
    client = _client(url, token)
    projects = _fetch_projects(client, project, prefix)
    _emit(issues_breakdown.build(dt.build_issues_from_projects(projects)), _out(output, "issues_breakdown", fmt), "Issues Breakdown")


# ─── debt ──────────────────────────────────────────────────────────────────
@cli.command()
@_common
def debt(url, token, output, fmt, project, prefix):
    """Technical debt heatmap — SQALE ratings (A–E) per project × dimension."""
    client = _client(url, token)
    projects = _fetch_projects(client, project, prefix)
    _emit(debt_heatmap.build(projects), _out(output, "debt_heatmap", fmt), "Technical Debt Heatmap")


# ─── coverage ──────────────────────────────────────────────────────────────
@cli.command()
@_common
def coverage(url, token, output, fmt, project, prefix):
    """Coverage & duplication landscape — bubble scatter plot."""
    client = _client(url, token)
    projects = _fetch_projects(client, project, prefix)
    _emit(coverage_landscape.build(projects), _out(output, "coverage_landscape", fmt), "Coverage & Duplication Landscape")


# ─── security ──────────────────────────────────────────────────────────────
@cli.command()
@_common
def security(url, token, output, fmt, project, prefix):
    """Security vulnerability distribution — OWASP breakdown, severity, hotspots."""
    client = _client(url, token)
    with Progress(SpinnerColumn(), TextColumn("{task.description}"), console=console) as prog:
        prog.add_task("Fetching security data…", total=None)
        sec_data = dt.fetch_security_data(client, _component_keys(client, project, prefix))
    _emit(security_dist.build(sec_data), _out(output, "security_dist", fmt), "Security Vulnerability Distribution")


# ─── trend ─────────────────────────────────────────────────────────────────
_DEFAULT_TREND_METRICS = ["bugs", "vulnerabilities", "coverage", "code_smells"]


@cli.command()
@click.argument("project_key")
@click.option("--url", envvar="SONAR_URL", required=True, help=_URL_HELP)
@click.option("--token", envvar="SONAR_TOKEN", required=True, help=_TOKEN_HELP)
@click.option("-o", "--output", default="sonar-reports", show_default=True)
@click.option("-f", "--format", "fmt", type=click.Choice(["html", "png"]), default="html")
@click.option(
    "-m", "--metric", "metrics",
    multiple=True,
    default=_DEFAULT_TREND_METRICS,
    show_default=True,
    help="Metric key to include (repeatable). "
         "Choices: bugs, vulnerabilities, code_smells, coverage, duplicated_lines_density, "
         "sqale_index, security_hotspots, ncloc",
)
@click.option("--from", "from_date", default=None, help="Start date YYYY-MM-DD")
def trend_cmd(project_key, url, token, output, fmt, metrics, from_date):
    """Trend over time for a single project — line chart of selected metrics."""
    client = _client(url, token)
    with Progress(SpinnerColumn(), TextColumn("{task.description}"), console=console) as prog:
        prog.add_task(f"Fetching history for {project_key}…", total=None)
        history = dt.fetch_trend(client, project_key, list(metrics), from_date)
    _emit(trend.build(history, project_key), _out(output, f"trend_{project_key}", fmt), f"Trend — {project_key}")


cli.add_command(trend_cmd, name="trend")


# ─── ownership ─────────────────────────────────────────────────────────────
@cli.command()
@click.option("--url", envvar="SONAR_URL", required=True, help=_URL_HELP)
@click.option("--token", envvar="SONAR_TOKEN", required=True, help=_TOKEN_HELP)
@click.option("-o", "--output", default="sonar-reports", show_default=True)
@click.option("-f", "--format", "fmt", type=click.Choice(["html", "png"]), default="html")
@click.option(
    "--teams", "teams_file", required=True, type=click.Path(exists=True),
    help="YAML file mapping team names to project keys.",
)
def ownership(url, token, output, fmt, teams_file):
    """Ownership & responsibility map — QG pass rate, debt, issues by team."""
    with open(teams_file, encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)
    teams = cfg.get("teams", [])
    if not teams:
        console.print("[red]No teams found in YAML file.[/red]")
        raise SystemExit(1)

    all_keys = [k for team in teams for k in team.get("projects", [])]
    client = _client(url, token)
    projects = _fetch_projects(client, None)

    _emit(ownership_map.build(teams, projects), _out(output, "ownership_map", fmt), "Ownership & Responsibility Map")


# ─── remediation ───────────────────────────────────────────────────────────
@cli.command()
@_common
def remediation(url, token, output, fmt, project, prefix):
    """Remediation effort estimate — hours by project, broken down by type."""
    client = _client(url, token)
    projects = _fetch_projects(client, project, prefix)
    _emit(remediation_chart.build(projects), _out(output, "remediation", fmt), "Remediation Effort Estimate")


# ─── radar ─────────────────────────────────────────────────────────────────
@cli.command()
@_common
def radar_cmd(url, token, output, fmt, project, prefix):
    """Per-project quality radar — Reliability, Security, Maintainability, Coverage, Duplication."""
    client = _client(url, token)
    projects = _fetch_projects(client, project, prefix)
    _emit(radar.build(projects), _out(output, "radar", fmt), "Project Quality Radars")


cli.add_command(radar_cmd, name="radar")


# ─── ratings ───────────────────────────────────────────────────────────────
@cli.command()
@_common
def ratings(url, token, output, fmt, project, prefix):
    """Portfolio ratings distribution — A–E breakdown for Reliability, Security, Maintainability."""
    client = _client(url, token)
    projects = _fetch_projects(client, project, prefix)
    _emit(ratings_distribution.build(projects), _out(output, "ratings_distribution", fmt), "Ratings Distribution")


# ─── risk ──────────────────────────────────────────────────────────────────
@cli.command()
@_common
def risk(url, token, output, fmt, project, prefix):
    """Risk matrix — bugs vs vulnerabilities scatter, sized by LOC, coloured by Quality Gate."""
    client = _client(url, token)
    projects = _fetch_projects(client, project, prefix)
    _emit(risk_matrix.build(projects), _out(output, "risk_matrix", fmt), "Risk Matrix")


# ─── violations ────────────────────────────────────────────────────────────
@cli.command()
@_common
def violations_cmd(url, token, output, fmt, project, prefix):
    """Violations breakdown — stacked bar of blocker/critical/major/minor/info per project."""
    client = _client(url, token)
    projects = _fetch_projects(client, project, prefix)
    _emit(violations.build(projects), _out(output, "violations", fmt), "Violations by Severity")


cli.add_command(violations_cmd, name="violations")


# ─── security-projects ─────────────────────────────────────────────────────
@cli.command("security-projects")
@_common
def security_projects_cmd(url, token, output, fmt, project, prefix):
    """Security vulnerability distribution per project — vulnerabilities, hotspots & remediation effort."""
    client = _client(url, token)
    projects = _fetch_projects(client, project, prefix)
    _emit(security_per_project.build(projects), _out(output, "security_per_project", fmt), "Security per Project")


# ─── debt-coverage ─────────────────────────────────────────────────────────
@cli.command("debt-coverage")
@_common
def debt_coverage_cmd(url, token, output, fmt, project, prefix):
    """Bubble chart: technical debt (days) vs coverage (%), sized by LOC, coloured by worst reliability/security rating."""
    client = _client(url, token)
    projects = _fetch_projects(client, project, prefix)
    _emit(debt_coverage.build(projects), _out(output, "debt_coverage", fmt), "Technische schuld vs. testdekking")


# ─── matrix ────────────────────────────────────────────────────────────────
@cli.command()
@_common
def matrix(url, token, output, fmt, project, prefix):
    """Aggregated project matrix — all key metrics as a colour-coded heatmap, projects sorted by score."""
    client = _client(url, token)
    projects = _fetch_projects(client, project, prefix)
    _emit(project_matrix.build(projects), _out(output, "project_matrix", fmt), "Aggregated Project Matrix")


# ─── git ───────────────────────────────────────────────────────────────────
@cli.command("git")
@click.option("-r", "--repo", "repos", multiple=True, default=(".",""), help="Path to git repository (repeatable)")
@click.option("--since", default="90 days ago", show_default=True, help="Start of history (git date format)")
@click.option("-o", "--output", default="sonar-reports", show_default=True, help="Output directory")
@click.option("-f", "--format", "fmt", type=click.Choice(["html", "png"]), default="html", show_default=True)
def git_cmd(repos, since, output, fmt):
    """Git history analysis — commits per day/author/repo, activity heatmap, cumulative growth.

    Accepts multiple --repo flags to combine several repositories into one report.
    """
    repo_list = [r for r in repos if r] or ["."]
    with Progress(SpinnerColumn(), TextColumn("{task.description}"), console=console) as prog:
        prog.add_task(f"Reading git log from {len(repo_list)} repo(s)…", total=None)
        try:
            commits, errors = git_data.fetch_multiple_repos(repo_list, since)
        except RuntimeError as exc:
            console.print(f"[red]Error:[/red] {exc}")
            raise SystemExit(1)
    for err in errors:
        console.print(f"[yellow]Warning:[/yellow] {err}")
    console.print(f"  {len(commits)} commits from {len(repo_list)} repo(s)")
    _emit(git_commits.build(commits), _out(output, "git_history", fmt), "Git History Analysis")


# ─── summary ───────────────────────────────────────────────────────────────
@cli.command()
@_common
def summary(url, token, output, fmt, project, prefix):
    """System summary table — modules, LOC, coverage, languages, costs, debt, bugs, security, duplication."""
    client = _client(url, token)
    projects = _fetch_projects(client, project, prefix)
    _emit(summary_table.build(projects), _out(output, "summary", fmt), "Systeemeigenschappen")


# ─── all ───────────────────────────────────────────────────────────────────
@cli.command("all")
@click.option("--url", envvar="SONAR_URL", required=True, help=_URL_HELP)
@click.option("--token", envvar="SONAR_TOKEN", required=True, help=_TOKEN_HELP)
@click.option("-o", "--output", default="sonar-reports", show_default=True)
@click.option("-f", "--format", "fmt", type=click.Choice(["html", "png"]), default="html")
@click.option("--teams", "teams_file", default=None, type=click.Path(exists=True), help="Teams YAML (optional)")
@click.option("--prefix", default=None, help="Restrict to projects whose key starts with this prefix")
def all_cmd(url, token, output, fmt, teams_file, prefix):
    """Generate all diagrams in one go."""
    client = _client(url, token)

    console.rule("[bold]Fetching project data")
    projects = _fetch_projects(client, None, prefix)
    keys_str = ",".join(p["key"] for p in projects) if prefix else None

    generated = []

    def _save(sections, name, title):
        paths = save_html(sections, _out(output, name, fmt), title)
        generated.extend(paths)
        console.print(f"  [green]✓[/green] {title}")

    console.rule("[bold]Generating charts")
    _save(health_overview.build(projects), "health_overview", "Per-Project Health Overview")
    _save(debt_heatmap.build(projects), "debt_heatmap", "Technical Debt Heatmap")
    _save(coverage_landscape.build(projects), "coverage_landscape", "Coverage & Duplication Landscape")
    _save(remediation_chart.build(projects), "remediation", "Remediation Effort Estimate")
    _save(radar.build(projects), "radar", "Project Quality Radars")
    _save(ratings_distribution.build(projects), "ratings_distribution", "Ratings Distribution")
    _save(risk_matrix.build(projects), "risk_matrix", "Risk Matrix")
    _save(violations.build(projects), "violations", "Violations by Severity")
    _save(security_per_project.build(projects), "security_per_project", "Security per Project")
    _save(project_matrix.build(projects), "project_matrix", "Aggregated Project Matrix")
    _save(debt_coverage.build(projects), "debt_coverage", "Technische schuld vs. testdekking")


    _save(issues_breakdown.build(dt.build_issues_from_projects(projects)), "issues_breakdown", "Issues Breakdown")
    _save(summary_table.build(projects), "summary", "Systeemeigenschappen")

    with Progress(SpinnerColumn(), TextColumn("{task.description}"), console=console) as prog:
        prog.add_task("Fetching security data…", total=None)
        sec_data = dt.fetch_security_data(client, keys_str)
    _save(security_dist.build(sec_data), "security_dist", "Security Vulnerability Distribution")

    if teams_file:
        with open(teams_file, encoding="utf-8") as fh:
            cfg = yaml.safe_load(fh)
        teams = cfg.get("teams", [])
        if teams:
            _save(ownership_map.build(teams, projects), "ownership_map", "Ownership & Responsibility Map")

    console.rule()
    console.print(f"\n[bold green]Done![/bold green] {len(generated)} files in [cyan]{output}/[/cyan]")
    for p in generated:
        console.print(f"  • {p}")
