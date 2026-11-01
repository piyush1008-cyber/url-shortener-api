from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import URLCreate, URLResponse
from app.crud import create_url, get_url_by_code, record_click, delete_url
from app.utils import is_url_expired
from app.config import settings

router = APIRouter(tags=["URLs"])


@router.post(
    "/api/v1/shorten",
    response_model=URLResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Shorten a destination URL",
    description="Generates a unique short code for a URL, supporting custom aliases and expiration periods."
)
def shorten_url(
    payload: URLCreate,
    db: Session = Depends(get_db)
):
    try:
        db_item, is_existing = create_url(db, payload)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )

    short_url = f"{settings.BASE_URL}/{db_item.short_code}"
    return URLResponse(
        id=db_item.id,
        original_url=db_item.original_url,
        short_code=db_item.short_code,
        short_url=short_url,
        created_at=db_item.created_at,
        expires_at=db_item.expires_at,
        click_count=db_item.click_count,
        is_active=db_item.is_active
    )


@router.get(
    "/{short_code}",
    response_class=RedirectResponse,
    status_code=status.HTTP_307_TEMPORARY_REDIRECT,
    summary="Redirect to original target URL",
    description="Looks up short code and redirects client while recording analytics telemetry in background."
)
def redirect_to_original(
    short_code: str,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    url_item = get_url_by_code(db, short_code, active_only=True)
    if not url_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Short URL with code '{short_code}' not found."
        )

    if is_url_expired(url_item.expires_at):
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="This shortened link has expired."
        )

    # Telemetry data extraction
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    referrer = request.headers.get("referer")

    background_tasks.add_task(
        record_click,
        db=db,
        url_item=url_item,
        ip_address=client_ip,
        user_agent=user_agent,
        referrer=referrer
    )

    return RedirectResponse(url=url_item.original_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)


@router.delete(
    "/api/v1/links/{short_code}",
    status_code=status.HTTP_200_OK,
    summary="Deactivate a shortened link",
    description="Soft-deletes an active short URL preventing subsequent redirections."
)
def deactivate_link(
    short_code: str,
    db: Session = Depends(get_db)
):
    success = delete_url(db, short_code)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Short URL with code '{short_code}' not found."
        )
    return {"status": "success", "message": f"Link '{short_code}' successfully deactivated."}
