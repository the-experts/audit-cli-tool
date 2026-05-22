import requests
from typing import Any, Dict, List, Optional


class SonarQubeError(Exception):
    pass


class SonarQubeClient:
    def __init__(self, url: str, token: str):
        self.base_url = url.rstrip("/")
        self.session = requests.Session()
        self.session.auth = (token, "")
        self.session.headers["Accept"] = "application/json"

    def _get(self, path: str, **params: Any) -> Dict:
        url = f"{self.base_url}{path}"
        resp = self.session.get(url, params={k: v for k, v in params.items() if v is not None})
        if not resp.ok:
            raise SonarQubeError(f"API {resp.status_code} on {path}: {resp.text[:300]}")
        return resp.json()

    def get_projects(self) -> List[Dict]:
        projects: List[Dict] = []
        page = 1
        while True:
            data = self._get("/api/components/search_projects", p=page, ps=500)
            projects.extend(data["components"])
            if len(projects) >= data["paging"]["total"]:
                break
            page += 1
        return projects

    def get_measures(self, component: str, metrics: List[str]) -> Dict[str, Optional[str]]:
        data = self._get(
            "/api/measures/component",
            component=component,
            metricKeys=",".join(metrics),
        )
        return {m["metric"]: m.get("value") for m in data["component"]["measures"]}

    def get_quality_gate_status(self, project_key: str) -> str:
        data = self._get("/api/qualitygates/project_status", projectKey=project_key)
        return data["projectStatus"]["status"]

    def get_issues(self, facets: str, component_keys: Optional[str] = None, **kwargs: Any) -> Dict:
        return self._get(
            "/api/issues/search",
            componentKeys=component_keys,
            facets=facets,
            ps=1,
            **kwargs,
        )

    def get_hotspots(self, project_key: Optional[str] = None, status: Optional[str] = None) -> Dict:
        return self._get(
            "/api/hotspots/search",
            projectKey=project_key,
            status=status,
            ps=1,
        )

    def get_history(
        self,
        component: str,
        metrics: List[str],
        from_date: Optional[str] = None,
    ) -> Dict[str, List]:
        data = self._get(
            "/api/measures/search_history",
            component=component,
            metrics=",".join(metrics),
            ps=1000,
            **{"from": from_date} if from_date else {},
        )
        return {
            m["metric"]: [(h["date"][:10], h.get("value")) for h in m["history"]]
            for m in data["measures"]
        }
