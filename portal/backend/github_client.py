"""
Purpose:
    GitHub Actions workflow dispatcher for the self-service portal.
    Uses a GitHub App installation token — never a PAT — to trigger
    workflow_dispatch events via the GitHub REST API.

Usage:
    client = GitHubActionsClient()
    run_id = client.trigger_workflow("promote.yml", inputs={"model_name": "fraud-detector"})

Dependencies:
    httpx>=0.27, PyJWT>=2.8
"""

from __future__ import annotations

import logging
import os
import time

import httpx
import jwt

logger = logging.getLogger(__name__)

_GITHUB_API = "https://api.github.com"
_REPO = os.environ.get("GITHUB_REPOSITORY", "")  # e.g. "org/mlops-playbook"
_APP_ID = os.environ.get("GITHUB_APP_ID", "")
_APP_PRIVATE_KEY = os.environ.get("GITHUB_APP_PRIVATE_KEY", "")  # PEM string
_INSTALLATION_ID = os.environ.get("GITHUB_INSTALLATION_ID", "")


class GitHubActionsClient:
    """
    Triggers GitHub Actions workflows via REST API using a GitHub App installation token.

    Never stores long-lived credentials.  Installation tokens are valid for 1 hour
    and are fetched fresh on each request.
    """

    def _get_jwt(self) -> str:
        now = int(time.time())
        payload = {"iat": now - 60, "exp": now + 600, "iss": _APP_ID}
        return jwt.encode(payload, _APP_PRIVATE_KEY, algorithm="RS256")

    def _get_installation_token(self) -> str:
        app_jwt = self._get_jwt()
        url = f"{_GITHUB_API}/app/installations/{_INSTALLATION_ID}/access_tokens"
        resp = httpx.post(
            url,
            headers={
                "Authorization": f"Bearer {app_jwt}",
                "Accept": "application/vnd.github+json",
            },
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()["token"]

    def trigger_workflow(
        self,
        workflow_id: str,
        inputs: dict[str, str],
        ref: str = "main",
    ) -> str:
        """
        Trigger a workflow_dispatch event.  Returns the workflow run URL.
        """
        token = self._get_installation_token()
        url = f"{_GITHUB_API}/repos/{_REPO}/actions/workflows/{workflow_id}/dispatches"
        resp = httpx.post(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
            },
            json={"ref": ref, "inputs": inputs},
            timeout=15,
        )
        resp.raise_for_status()
        logger.info("Triggered workflow %s with inputs %s", workflow_id, inputs)
        return f"https://github.com/{_REPO}/actions/workflows/{workflow_id}"
