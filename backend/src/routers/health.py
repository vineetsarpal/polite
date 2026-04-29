from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    """
    Static health check used by Render's healthCheckPath.

    Deliberately does NOT touch the database. A DB-touching health check
    would be filtered to zero rows by RLS (no app.current_org_id is set
    on this anonymous request) and would return misleading-but-passing.
    DB liveness is covered by Sentry + Better Stack in sub-project #5.
    """
    return {"status": "ok"}
