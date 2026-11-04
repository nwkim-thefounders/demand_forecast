"""로그인 이메일 형식 검증 테스트."""

from typing import Any

import pytest
import streamlit as st


def _import_login(monkeypatch: pytest.MonkeyPatch) -> Any:
    """실제 secrets.toml 없이 로그인 모듈을 가져온다."""
    import importlib
    import sys

    monkeypatch.setattr(
        st,
        "secrets",
        {
            "slack": {
                "client_id": "x",
                "client_secret": "x",
                "redirect_uri": "http://localhost",
            }
        },
    )
    monkeypatch.delitem(sys.modules, "app_01_login", raising=False)
    return importlib.import_module("app_01_login")


@pytest.mark.parametrize(
    "email",
    ["user.name+tag@example-domain.com", "a_b@example.kr"],
)
def test_check_email_accepts_supported_addresses(
    monkeypatch: pytest.MonkeyPatch,
    email: str,
) -> None:
    """유효한 이메일의 점, 밑줄, 더하기, 하이픈을 허용한다."""
    login = _import_login(monkeypatch)
    session: dict[str, Any] = {"input_em": email}
    monkeypatch.setattr(st, "session_state", session)

    login.check_email()

    assert session["is_valueable"] is True
    assert session["login_warning_msg"] == ""


@pytest.mark.parametrize(
    "email",
    [
        "user/name@example.com",
        "user:name@example.com",
        "user@example-.com",
        "user@-example.com",
        "user@example..com",
    ],
)
def test_check_email_rejects_punctuation_and_malformed_domain(
    monkeypatch: pytest.MonkeyPatch,
    email: str,
) -> None:
    """문자 범위에 잘못 포함된 문장부호와 불완전한 도메인을 거부한다."""
    login = _import_login(monkeypatch)
    session: dict[str, Any] = {"input_em": email}
    monkeypatch.setattr(st, "session_state", session)

    login.check_email()

    assert session["is_valueable"] is False
    assert session["login_warning_msg"] == "올바른 이메일 형식이 아닙니다."
