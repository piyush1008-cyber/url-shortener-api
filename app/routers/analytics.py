from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import URLAnalytics
from app.crud import get_url_by_code, get_url_analytics

router = APIRouter(prefix="/api/v1/analytics", tags=["Analytics"])


@router.get(
    "/{short_code}",
    response_model=URLAnalytics,
    status_code=status.HTTP_200_OK,
    summary="Retrieve click analytics for a short URL",
    description="Returns aggregate click metrics, time-to-live status, top referrer domains, and recent click timestamps."
)
def get_analytics(
    short_code: str,
    db: Session = Depends(get_db)
):
    url_item = get_url_by_code(db, short_code, active_only=False)
    if not url_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"URL with code '{short_code}' not found."
        )

    return get_url_analytics(db, url_item)
