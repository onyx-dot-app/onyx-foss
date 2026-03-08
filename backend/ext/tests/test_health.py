"""Tests for ext health endpoint response logic.

Run in Docker where all dependencies are available:
  docker exec onyx-api_server-1 python -m pytest /app/ext/tests/ -xv
"""

import importlib
import os
from unittest.mock import patch

import ext.config
import ext.routers.health


class TestExtHealthEndpoint:
    """Test health endpoint response structure."""

    def _call_health(self) -> dict:
        """Reload config + health module and call the function."""
        importlib.reload(ext.config)
        importlib.reload(ext.routers.health)
        return ext.routers.health.ext_health_check(_=None)

    def test_health_returns_ok_status(self) -> None:
        with patch.dict(os.environ, {"EXT_ENABLED": "true"}, clear=True):
            result = self._call_health()
            assert result["status"] == "ok"

    def test_health_returns_ext_enabled_flag(self) -> None:
        with patch.dict(os.environ, {"EXT_ENABLED": "true"}, clear=True):
            result = self._call_health()
            assert "ext_enabled" in result
            assert result["ext_enabled"] is True

    def test_health_returns_all_module_flags(self) -> None:
        with patch.dict(os.environ, {"EXT_ENABLED": "true"}, clear=True):
            result = self._call_health()
            expected_modules = [
                "token_limits",
                "rbac",
                "analytics",
                "branding",
                "custom_prompts",
                "doc_access",
            ]
            for module in expected_modules:
                assert module in result["modules"], f"Missing module: {module}"

    def test_health_modules_default_false(self) -> None:
        with patch.dict(os.environ, {"EXT_ENABLED": "true"}, clear=True):
            result = self._call_health()
            for module_name, enabled in result["modules"].items():
                assert enabled is False, f"{module_name} should be False"

    def test_health_shows_enabled_module(self) -> None:
        with patch.dict(
            os.environ,
            {"EXT_ENABLED": "true", "EXT_ANALYTICS_ENABLED": "true"},
            clear=True,
        ):
            result = self._call_health()
            assert result["modules"]["analytics"] is True
            assert result["modules"]["token_limits"] is False
