from datetime import datetime, timezone
from collections import Counter
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models import URLItem, ClickLog
from app.schemas import URLCreate, URLAnalytics, ClickDetail, URLResponse
from app.utils import generate_short_code, compute_expiration, is_url_expired
from app.config import settings


def get_url_by_code(db: Session, short_code: str, active_only: bool = True) -> Optional[URLItem]:
    """Retrieve URL record by its unique short code."""
    query = db.query(URLItem).filter(URLItem.short_code == short_code)
    if active_only:
        query = query.filter(URLItem.is_active == True)
    return query.first()


def create_url(db: Session, url_in: URLCreate) -> Tuple[URLItem, bool]:
    """
    Create a new shortened URL entry.
    Returns (URLItem, is_existing).
    Raises ValueError if custom alias is already reserved.
    """
    # 1. Custom vanity code requested
    if url_in.custom_code:
        existing = db.query(URLItem).filter(URLItem.short_code == url_in.custom_code).first()
        if existing:
            raise ValueError(f"Custom code '{url_in.custom_code}' is already in use.")
        code = url_in.custom_code
    else:
        # Check if identical original_url with no expiration already exists
        if url_in.expires_in_days is None:
            existing = db.query(URLItem).filter(
                URLItem.original_url == url_in.original_url,
                URLItem.expires_at == None,
                URLItem.is_active == True
            ).first()
            if existing:
                return existing, True

        # Generate unique code with collision avoidance
        for _ in range(5):
            candidate = generate_short_code(settings.SHORT_CODE_LENGTH)
            if not db.query(URLItem).filter(URLItem.short_code == candidate).first():
                code = candidate
                break
        else:
            code = generate_short_code(settings.SHORT_CODE_LENGTH + 2)

    expires_at = compute_expiration(url_in.expires_in_days)

    db_item = URLItem(
        original_url=url_in.original_url,
        short_code=code,
        created_at=datetime.now(timezone.utc),
        expires_at=expires_at,
        click_count=0,
        is_active=True
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item, False


def record_click(
    db: Session,
    url_item: URLItem,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    referrer: Optional[str] = None
) -> None:
    """Record an access click event and increment aggregate click counter."""
    url_item.click_count += 1
    click_entry = ClickLog(
        url_id=url_item.id,
        clicked_at=datetime.now(timezone.utc),
        ip_address=ip_address,
        user_agent=user_agent,
        referrer=referrer
    )
    db.add(click_entry)
    db.commit()


def get_url_analytics(db: Session, url_item: URLItem) -> URLAnalytics:
    """Compile click metrics, top referrers, and recent access logs."""
    logs = db.query(ClickLog).filter(ClickLog.url_id == url_item.id).order_by(desc(ClickLog.clicked_at)).all()

    # Tally referrers
    referrers = [l.referrer for l in logs if l.referrer]
    ref_counts = dict(Counter(referrers).most_common(5))
    if not ref_counts and logs:
        ref_counts = {"Direct / None": len(logs)}

    recent_details = [
        ClickDetail(
            clicked_at=l.clicked_at,
            referrer=l.referrer,
            user_agent=l.user_agent,
            ip_address=l.ip_address
        )
        for l in logs[:10]
    ]

    short_url = f"{settings.BASE_URL}/{url_item.short_code}"

    return URLAnalytics(
        short_code=url_item.short_code,
        original_url=url_item.original_url,
        short_url=short_url,
        total_clicks=url_item.click_count,
        created_at=url_item.created_at,
        expires_at=url_item.expires_at,
        is_expired=is_url_expired(url_item.expires_at),
        top_referrers=ref_counts,
        recent_clicks=recent_details
    )


def delete_url(db: Session, short_code: str) -> bool:
    """Soft-delete URL by setting is_active = False."""
    item = db.query(URLItem).filter(URLItem.short_code == short_code).first()
    if not item:
        return False
    item.is_active = False
    db.commit()
    return True
