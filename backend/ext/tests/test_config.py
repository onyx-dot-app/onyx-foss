"""Tests for ext.config feature flags."""

import os
from unittest.mock import patch


class TestExtConfig:
    """Test feature flag logic."""

    def test_all_flags_false_by_default(self) -> None:
        """All flags should be false when no env vars are set."""
        with patch.dict(os.environ, {}, clear=True):
            # Re-import to pick up fresh env
            import importlib

            import ext.config

            importlib.reload(ext.config)

            assert ext.config.EXT_ENABLED is False
            assert ext.config.EXT_TOKEN_LIMITS_ENABLED is False
            assert ext.config.EXT_RBAC_ENABLED is False
            assert ext.config.EXT_ANALYTICS_ENABLED is False
            assert ext.config.EXT_BRANDING_ENABLED is False
            assert ext.config.EXT_CUSTOM_PROMPTS_ENABLED is False
            assert ext.config.EXT_DOC_ACCESS_ENABLED is False

    def test_ext_enabled_alone(self) -> None:
        """EXT_ENABLED=true alone should not enable any module."""
        with patch.dict(os.environ, {"EXT_ENABLED": "true"}, clear=True):
            import importlib

            import ext.config

            importlib.reload(ext.config)

            assert ext.config.EXT_ENABLED is True
            assert ext.config.EXT_TOKEN_LIMITS_ENABLED is False
            assert ext.config.EXT_RBAC_ENABLED is False
            assert ext.config.EXT_ANALYTICS_ENABLED is False

    def test_module_flag_requires_ext_enabled(self) -> None:
        """Individual module flags are AND-gated with EXT_ENABLED."""
        # Module flag true but master switch false → module stays false
        with patch.dict(
            os.environ,
            {"EXT_ENABLED": "false", "EXT_TOKEN_LIMITS_ENABLED": "true"},
            clear=True,
        ):
            import importlib

            import ext.config

            importlib.reload(ext.config)

            assert ext.config.EXT_ENABLED is False
            assert ext.config.EXT_TOKEN_LIMITS_ENABLED is False

    def test_module_flag_enabled_when_both_true(self) -> None:
        """Module flag should be true when both master and module flags are true."""
        with patch.dict(
            os.environ,
            {"EXT_ENABLED": "true", "EXT_TOKEN_LIMITS_ENABLED": "true"},
            clear=True,
        ):
            import importlib

            import ext.config

            importlib.reload(ext.config)

            assert ext.config.EXT_ENABLED is True
            assert ext.config.EXT_TOKEN_LIMITS_ENABLED is True

    def test_case_insensitive(self) -> None:
        """Flag parsing should be case-insensitive."""
        with patch.dict(
            os.environ,
            {"EXT_ENABLED": "True", "EXT_ANALYTICS_ENABLED": "TRUE"},
            clear=True,
        ):
            import importlib

            import ext.config

            importlib.reload(ext.config)

            assert ext.config.EXT_ENABLED is True
            assert ext.config.EXT_ANALYTICS_ENABLED is True
