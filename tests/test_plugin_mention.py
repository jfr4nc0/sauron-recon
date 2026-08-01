from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from plugins.sauron_recon_telegram import _get_bot_username, _is_mentioned


def test_mention_detection_with_at():
    with patch.dict(os.environ, {"TELEGRAM_BOT_USERNAME": "sauron_reconn_bot"}):
        assert _is_mentioned("@sauron_reconn_bot buscá depósitos", "sauron_reconn_bot") is True
        assert _is_mentioned("hola @sauron_reconn_bot", "sauron_reconn_bot") is True


def test_mention_detection_with_slash_command():
    with patch.dict(os.environ, {"TELEGRAM_BOT_USERNAME": "sauron_reconn_bot"}):
        assert _is_mentioned("/start", "sauron_reconn_bot") is True
        assert _is_mentioned("/start@bot", "sauron_reconn_bot") is True


def test_no_mention_in_plain_group_message():
    with patch.dict(os.environ, {"TELEGRAM_BOT_USERNAME": "sauron_reconn_bot"}):
        assert _is_mentioned("alguien sabe cuanto cuesta un depósito?", "sauron_reconn_bot") is False
        assert _is_mentioned("hola gente", "sauron_reconn_bot") is False
        assert _is_mentioned("", "sauron_reconn_bot") is False


def test_case_insensitive_mention():
    with patch.dict(os.environ, {"TELEGRAM_BOT_USERNAME": "sauron_reconn_bot"}):
        assert _is_mentioned("@Sauron_Reconn_Bot buscá", "sauron_reconn_bot") is True


def test_get_bot_username_strips_at_prefix():
    with patch.dict(os.environ, {"TELEGRAM_BOT_USERNAME": "@sauron_reconn_bot"}):
        assert _get_bot_username() == "sauron_reconn_bot"
    with patch.dict(os.environ, {"TELEGRAM_BOT_USERNAME": "sauron_reconn_bot"}):
        assert _get_bot_username() == "sauron_reconn_bot"
    with patch.dict(os.environ, {}, clear=True):
        assert _get_bot_username() == ""
