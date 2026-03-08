"""Extension health check endpoint."""

from fastapi import APIRouter
from fastapi import Depends

from onyx.auth.users import current_user
from onyx.db.models import User

from ext.config import EXT_ANALYTICS_ENABLED
from ext.config import EXT_BRANDING_ENABLED
from ext.config import EXT_CUSTOM_PROMPTS_ENABLED
from ext.config import EXT_DOC_ACCESS_ENABLED
from ext.config import EXT_ENABLED
from ext.config import EXT_TOKEN_LIMITS_ENABLED
from ext.config import EXT_RBAC_ENABLED

router = APIRouter(prefix="/ext", tags=["ext"])


@router.get("/health")
def ext_health_check(
    _: User | None = Depends(current_user),
) -> dict:
    """Returns extension framework status and enabled modules."""
    return {
        "status": "ok",
        "ext_enabled": EXT_ENABLED,
        "modules": {
            "token_limits": EXT_TOKEN_LIMITS_ENABLED,
            "rbac": EXT_RBAC_ENABLED,
            "analytics": EXT_ANALYTICS_ENABLED,
            "branding": EXT_BRANDING_ENABLED,
            "custom_prompts": EXT_CUSTOM_PROMPTS_ENABLED,
            "doc_access": EXT_DOC_ACCESS_ENABLED,
        },
    }
