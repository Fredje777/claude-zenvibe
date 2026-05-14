"""Smart bilingual dispatch in the MCP server."""
import sys
from pathlib import Path

# Allow importing the MCP server module
SERVER_DIR = Path(__file__).parent.parent / "mcp"
sys.path.insert(0, str(SERVER_DIR))

import server  # noqa: E402


def test_messages_dict_has_en_and_fr():
    """MESSAGES must define both languages."""
    assert "en" in server.MESSAGES
    assert "fr" in server.MESSAGES


def test_messages_have_same_keys():
    """EN and FR dicts must define the same keys (no missing translation)."""
    en_keys = set(server.MESSAGES["en"].keys())
    fr_keys = set(server.MESSAGES["fr"].keys())
    assert en_keys == fr_keys, f"Mismatch: EN={en_keys - fr_keys}, FR={fr_keys - en_keys}"


def test_t_returns_en_by_default():
    assert server._t("safe_to_compact", "en").startswith("🧘 It's safe")


def test_t_returns_fr_when_requested():
    assert "compacter" in server._t("safe_to_compact", "fr").lower()


def test_t_falls_back_to_en_on_unknown_language():
    """Unknown language code falls back to English (no crash)."""
    assert server._t("safe_to_compact", "xx") == server._t("safe_to_compact", "en")


def test_t_raises_on_unknown_key():
    """An unknown message key is a programming error and should raise."""
    import pytest
    with pytest.raises(KeyError):
        server._t("nonexistent_key", "en")
