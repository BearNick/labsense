from fastapi import APIRouter, Depends

from app.config import Settings, get_settings

router = APIRouter(prefix="/payments", tags=["payments"])


@router.get("/links")
async def payment_links(settings: Settings = Depends(get_settings)) -> dict[str, str | None]:
    return {
        "stripe": settings.stripe_payment_url,
        "paypal": settings.paypal_payment_url,
        "telegram_stars": settings.telegram_stars_url or "placeholder"
    }
