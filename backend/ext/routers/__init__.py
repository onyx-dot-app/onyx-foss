"""Extension router registration.

Registers all enabled extension routers with the FastAPI application.
Uses the same include_router_with_global_prefix_prepended() pattern as Onyx.
"""

import logging

from fastapi import FastAPI

logger = logging.getLogger("ext")


def register_ext_routers(application: FastAPI) -> None:
    """Register all enabled extension routers."""
    # Import inside function to avoid circular import with onyx.main
    from onyx.main import include_router_with_global_prefix_prepended

    from ext.config import EXT_ENABLED

    if not EXT_ENABLED:
        return

    # Health check is always available when EXT_ENABLED
    from ext.routers.health import router as ext_health_router

    include_router_with_global_prefix_prepended(application, ext_health_router)
    logger.info("Extension health router registered")

    # ext-branding: Whitelabel/Branding
    from ext.config import EXT_BRANDING_ENABLED

    if EXT_BRANDING_ENABLED:
        from ext.routers.branding import admin_router as branding_admin_router
        from ext.routers.branding import public_router as branding_public_router

        # Mark public branding endpoints as unauthenticated so login page
        # can display custom branding before any user is logged in.
        # Runtime list mutation — no Onyx source file changes needed.
        from onyx.server.auth_check import PUBLIC_ENDPOINT_SPECS

        PUBLIC_ENDPOINT_SPECS.extend(
            [
                ("/enterprise-settings", {"GET"}),
                ("/enterprise-settings/logo", {"GET"}),
            ]
        )

        include_router_with_global_prefix_prepended(
            application, branding_public_router
        )
        include_router_with_global_prefix_prepended(
            application, branding_admin_router
        )
        logger.info("Extension branding routers registered")

    # Future module routers will be registered here behind their flags:
    # from ext.config import EXT_TOKEN_LIMITS_ENABLED
    # if EXT_TOKEN_LIMITS_ENABLED:
    #     from ext.routers.token_limits import router as token_limits_router
    #     include_router_with_global_prefix_prepended(application, token_limits_router)
