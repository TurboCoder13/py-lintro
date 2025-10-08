"""Tests for the GHCR prune untagged utility script."""

from __future__ import annotations

from typing import Any

from scripts.ci.ghcr_prune_untagged import (
    GhcrVersion,
    delete_version,
    list_container_versions,
    main,
)


def test_version_dataclass():
    """Construct ``GhcrVersion`` and validate fields are populated."""
    v = GhcrVersion(id=123, tags=["latest"])  # type: ignore[call-arg]
    assert v.id == 123
    assert v.tags == ["latest"]


def test_list_container_versions_parses_minimal_structure(monkeypatch):
    """Parse a minimal response structure into version objects.

    Args:
        monkeypatch: Pytest monkeypatch fixture (not used).
    """

    class DummyResp:
        def __init__(self, data: list[dict[str, Any]]):
            self._data = data

        def raise_for_status(self) -> None:  # pragma: no cover
            return

        def json(self) -> list[dict[str, Any]]:
            return self._data

    class DummyClient:
        def get(self, url: str, headers: dict[str, str]) -> DummyResp:  # noqa: ARG002
            return DummyResp(
                data=[
                    {"id": 1, "metadata": {"container": {"tags": ["latest"]}}},
                    {"id": 2, "metadata": {"container": {"tags": []}}},
                ],
            )

    versions = list_container_versions(client=DummyClient(), owner="owner")
    assert [v.id for v in versions] == [1, 2]
    assert versions[0].tags == ["latest"]
    assert versions[1].tags == []


def test_delete_version_calls_delete(monkeypatch):
    """Call delete and ensure correct endpoint is used.

    Args:
        monkeypatch: Pytest monkeypatch fixture (not used).
    """
    calls: list[tuple[str, dict[str, str]]] = []

    class DummyResp:
        status_code = 204

        def raise_for_status(self) -> None:  # pragma: no cover
            raise AssertionError("should not be called for 204")

    class DummyClient:
        def delete(
            self,
            url: str,
            headers: dict[str, str],
        ) -> DummyResp:  # noqa: ARG002
            calls.append((url, headers))
            return DummyResp()

    delete_version(client=DummyClient(), owner="owner", version_id=42)
    assert calls and "versions/42" in calls[0][0]


def test_delete_version_raises_on_non_204_non_404():
    """Raise when the delete operation returns an unexpected status code.

    Raises:
        AssertionError: If the expected RuntimeError is not raised.
    """

    class DummyResp:
        status_code = 500

        def raise_for_status(self) -> None:
            raise RuntimeError("boom")

    class DummyClient:
        def delete(
            self,
            url: str,
            headers: dict[str, str],
        ) -> DummyResp:  # noqa: ARG002
            return DummyResp()

    try:
        delete_version(client=DummyClient(), owner="owner", version_id=1)
    except RuntimeError:
        return
    raise AssertionError("Expected RuntimeError on non-204/404 response")


def test_main_deletes_only_untagged(monkeypatch):
    """Delete only untagged versions using the main entry point.

    Args:
        monkeypatch: Pytest monkeypatch fixture for environment and client.
    """
    deleted: list[int] = []

    class DummyRespGet:
        def __init__(self) -> None:
            self.status_code = 200

        def raise_for_status(self) -> None:  # pragma: no cover
            return

        def json(self) -> list[dict[str, Any]]:
            return [
                {
                    "id": 11,
                    "created_at": "2025-08-24T10:00:00Z",
                    "metadata": {"container": {"tags": ["latest"]}},
                },
                {
                    "id": 22,
                    "created_at": "2025-08-24T09:00:00Z",
                    "metadata": {"container": {"tags": []}},
                },
                {
                    "id": 33,
                    "created_at": "2025-08-24T08:00:00Z",
                    "metadata": {"container": {"tags": ["0.4.1"]}},
                },
                {
                    "id": 44,
                    "created_at": "2025-08-24T07:00:00Z",
                    "metadata": {"container": {"tags": []}},
                },
            ]

    class DummyRespDelete:
        def __init__(self) -> None:
            self.status_code = 204

        def raise_for_status(self) -> None:  # pragma: no cover
            return

    class DummyClient:
        def __init__(
            self,
            headers: dict[str, str],
            timeout: int,
        ) -> None:  # noqa: ARG002
            pass

        def __enter__(self) -> "DummyClient":  # type: ignore[name-defined]
            return self

        def __exit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001
            return None

        def get(
            self,
            url: str,
            headers: dict[str, str],
        ) -> DummyRespGet:  # noqa: ARG002
            return DummyRespGet()

        def delete(
            self,
            url: str,
            headers: dict[str, str],
        ) -> DummyRespDelete:  # noqa: ARG002
            # Extract trailing id
            deleted.append(int(url.rstrip("/").split("/")[-1]))
            return DummyRespDelete()

    # Patch httpx.Client used inside the module
    import scripts.ci.ghcr_prune_untagged as mod

    monkeypatch.setenv("GITHUB_TOKEN", "x")
    monkeypatch.setenv("GITHUB_REPOSITORY", "owner/name")
    monkeypatch.setattr(mod, "httpx", type("HX", (), {"Client": DummyClient}))

    rc = main()
    assert rc == 0
    # Only untagged IDs 22 and 44 should be deleted
    assert sorted(deleted) == [22, 44]


def test_main_respects_keep_n_and_dry_run(monkeypatch):
    """Respect keep-N and dry-run options when pruning.

    Args:
        monkeypatch: Pytest monkeypatch fixture for environment and client.
    """
    deleted: list[int] = []

    class DummyRespGet:
        def __init__(self) -> None:
            self.status_code = 200

        def raise_for_status(self) -> None:  # pragma: no cover
            return

        def json(self) -> list[dict[str, Any]]:
            # 3 untagged, descending by created_at
            return [
                {
                    "id": 100,
                    "created_at": "2025-08-24T12:00:00Z",
                    "metadata": {"container": {"tags": []}},
                },
                {
                    "id": 200,
                    "created_at": "2025-08-24T11:00:00Z",
                    "metadata": {"container": {"tags": []}},
                },
                {
                    "id": 300,
                    "created_at": "2025-08-24T10:00:00Z",
                    "metadata": {"container": {"tags": []}},
                },
            ]

    class DummyRespDelete:
        def __init__(self) -> None:
            self.status_code = 204

        def raise_for_status(self) -> None:  # pragma: no cover
            return

    class DummyClient:
        def __init__(
            self,
            headers: dict[str, str],
            timeout: int,
        ) -> None:  # noqa: ARG002
            pass

        def __enter__(self) -> "DummyClient":  # type: ignore[name-defined]
            return self

        def __exit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001
            return None

        def get(
            self,
            url: str,
            headers: dict[str, str],
        ) -> DummyRespGet:  # noqa: ARG002
            return DummyRespGet()

        def delete(
            self,
            url: str,
            headers: dict[str, str],
        ) -> DummyRespDelete:  # noqa: ARG002
            deleted.append(int(url.rstrip("/").split("/")[-1]))
            return DummyRespDelete()

    import scripts.ci.ghcr_prune_untagged as mod

    # Dry-run with keep 2 -> no deletions performed
    monkeypatch.setenv("GITHUB_TOKEN", "x")
    monkeypatch.setenv("GITHUB_REPOSITORY", "owner/name")
    monkeypatch.setenv("GHCR_PRUNE_DRY_RUN", "1")
    monkeypatch.setenv("GHCR_PRUNE_KEEP_UNTAGGED_N", "2")
    monkeypatch.setattr(mod, "httpx", type("HX", (), {"Client": DummyClient}))
    rc = main()
    assert rc == 0
    # Keep 2 newest untagged (100, 200). Would delete only 300; dry-run prevents it
    assert deleted == []
