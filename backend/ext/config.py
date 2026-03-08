"""VÖB Extension Feature Flags.

All flags default to false (disabled).
EXT_ENABLED is the master switch — if false, nothing loads.
Individual module flags are AND-gated with EXT_ENABLED.
"""

import os

EXT_ENABLED: bool = os.getenv("EXT_ENABLED", "false").lower() == "true"

# Individual module flags (all gated behind EXT_ENABLED)
EXT_TOKEN_LIMITS_ENABLED: bool = (
    EXT_ENABLED
    and os.getenv("EXT_TOKEN_LIMITS_ENABLED", "false").lower() == "true"
)
EXT_RBAC_ENABLED: bool = (
    EXT_ENABLED
    and os.getenv("EXT_RBAC_ENABLED", "false").lower() == "true"
)
EXT_ANALYTICS_ENABLED: bool = (
    EXT_ENABLED
    and os.getenv("EXT_ANALYTICS_ENABLED", "false").lower() == "true"
)
EXT_BRANDING_ENABLED: bool = (
    EXT_ENABLED
    and os.getenv("EXT_BRANDING_ENABLED", "false").lower() == "true"
)
EXT_CUSTOM_PROMPTS_ENABLED: bool = (
    EXT_ENABLED
    and os.getenv("EXT_CUSTOM_PROMPTS_ENABLED", "false").lower() == "true"
)
EXT_DOC_ACCESS_ENABLED: bool = (
    EXT_ENABLED
    and os.getenv("EXT_DOC_ACCESS_ENABLED", "false").lower() == "true"
)
