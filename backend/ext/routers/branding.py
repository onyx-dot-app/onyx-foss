"""FastAPI router for ext-branding (Whitelabel/Branding).

Registers on /enterprise-settings (same path the FOSS frontend expects).
This lets existing FOSS components (Logo.tsx, layout.tsx, SidebarWrapper, etc.)
load branding data automatically — zero frontend component changes needed.
"""

import logging

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session

from onyx.auth.users import current_admin_user
from onyx.db.engine.sql_engine import get_session
from onyx.db.models import User

from ext.schemas.branding import BrandingConfigResponse
from ext.schemas.branding import BrandingConfigUpdate
from ext.services.branding import get_branding_config
from ext.services.branding import get_logo
from ext.services.branding import update_branding_config
from ext.services.branding import update_logo

logger = logging.getLogger("ext.branding")

# Public endpoints (any authenticated user)
public_router = APIRouter(prefix="/enterprise-settings", tags=["ext-branding"])

# Admin endpoints
admin_router = APIRouter(
    prefix="/admin/enterprise-settings", tags=["ext-branding-admin"]
)


# --- Public endpoints ---


@public_router.get("")
def get_enterprise_settings(
    db_session: Session = Depends(get_session),
) -> BrandingConfigResponse:
    return get_branding_config(db_session)


@public_router.get("/logo")
def get_enterprise_logo(
    db_session: Session = Depends(get_session),
) -> Response:
    result = get_logo(db_session)
    if result is None:
        raise HTTPException(status_code=404, detail="No custom logo configured")

    data, content_type = result
    return Response(
        content=data,
        media_type=content_type,
        headers={
            "Cache-Control": "public, max-age=3600",
            "Content-Disposition": "inline",
        },
    )


# --- Admin endpoints ---


@admin_router.get("")
def admin_get_enterprise_settings(
    _: User = Depends(current_admin_user),
    db_session: Session = Depends(get_session),
) -> BrandingConfigResponse:
    return get_branding_config(db_session)


@admin_router.put("")
def admin_put_enterprise_settings(
    data: BrandingConfigUpdate,
    _: User = Depends(current_admin_user),
    db_session: Session = Depends(get_session),
) -> None:
    update_branding_config(db_session, data)


@admin_router.put("/logo")
async def admin_put_enterprise_logo(
    file: UploadFile,
    _: User = Depends(current_admin_user),
    db_session: Session = Depends(get_session),
) -> None:
    file_data = await file.read()
    error = update_logo(db_session, file_data, file.filename or "logo")
    if error:
        raise HTTPException(status_code=400, detail=error)
