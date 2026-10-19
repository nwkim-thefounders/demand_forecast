"""Snowflake 사용자 조회 실패 시 로그인 화면 복구 동작 테스트."""

from typing import Any

import pytest
import streamlit as st
from sqlalchemy.exc import DatabaseError, SQLAlchemyError


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


def test_connection_error_shows_safe_error_and_retry_without_auth(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """연결 오류는 안전한 안내를 보이고 사용자 세션을 인증하지 않는다."""
    login = _import_login(monkeypatch)
    session: dict[str, Any] = {}
    monkeypatch.setattr(st, "session_state", session)
    original_error = RuntimeError("private host detail")
    original_error.errno = 250001  # type: ignore[attr-defined]

    def _fail_load() -> object:
        raise DatabaseError("select", {}, original_error)

    monkeypatch.setattr(login.app_cache_load, "load_users_data", _fail_load)
    errors: list[str] = []
    buttons: list[tuple[str, Any]] = []
    monkeypatch.setattr(st, "error", errors.append)
    def _record_button(label: str, **kwargs: Any) -> bool:
        buttons.append((label, kwargs))
        return False

    monkeypatch.setattr(st, "button", _record_button)

    login.show_login()

    assert errors == [login.USER_DATA_LOAD_ERROR]
    assert buttons and buttons[0][0] == "다시 시도"
    assert "private host detail" not in errors[0]
    assert "DatabaseError" in caplog.text
    assert "250001" in caplog.text
    assert "private host detail" not in caplog.text
    assert "user_data" not in session
    assert "authentication_status" not in session


def test_retry_clears_cached_session_and_reruns_then_loads_users(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """재시도 콜백은 캐시와 세션을 비우고 다음 실행에서 정상 복구한다."""
    login = _import_login(monkeypatch)
    session: dict[str, Any] = {}
    monkeypatch.setattr(st, "session_state", session)
    calls = 0

    def _load() -> object:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise SQLAlchemyError("connection failed")
        return object()

    cache_clears: list[bool] = []
    reruns: list[bool] = []
    callback: list[Any] = []
    monkeypatch.setattr(login.app_cache_load, "load_users_data", _load)
    def _clear_cache() -> None:
        cache_clears.append(True)

    monkeypatch.setattr(login.app_cache_load, "clear_users_cache", _clear_cache)
    monkeypatch.setattr(st, "error", lambda message: None)

    def _button(label: str, **kwargs: Any) -> bool:
        callback.append(kwargs.get("on_click"))
        return False

    monkeypatch.setattr(st, "button", _button)
    monkeypatch.setattr(st, "rerun", lambda: reruns.append(True))
    login.show_login()
    assert callback[0] is not None
    callback[0]()
    assert cache_clears == [True]
    assert reruns == [True]
    assert "user_data" not in session

    # Streamlit의 rerun을 모사해 재실행하면 정상 데이터가 세션에 적재된다.
    monkeypatch.setattr(st, "button", lambda label, **kwargs: False)
    login.show_login()
    assert calls == 2
    assert "user_data" in session


def test_normal_user_data_load_keeps_existing_login_ui(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """정상 로딩은 기존 외부 사용자 로그인 UI 흐름을 유지한다."""
    login = _import_login(monkeypatch)
    session: dict[str, Any] = {}
    monkeypatch.setattr(st, "session_state", session)
    expected = object()
    monkeypatch.setattr(login.app_cache_load, "load_users_data", lambda: expected)
    monkeypatch.setattr(st, "query_params", {})
    # 초기 UI가 계속 구성됨을 확인하고 이후 세션 상태를 최소 구현한다.
    def _columns(*_args: object) -> tuple[_NullContext, _NullContext, _NullContext]:
        return (_NullContext(), _NullContext(), _NullContext())

    monkeypatch.setattr(st, "columns", _columns)
    monkeypatch.setattr(st, "container", lambda **_: _NullContext())
    monkeypatch.setattr(st, "expander", lambda *_: _NullContext())
    monkeypatch.setattr(st, "title", lambda *_: None)
    monkeypatch.setattr(st, "write", lambda *_: None)
    monkeypatch.setattr(st, "markdown", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(st, "text_input", lambda **_: None)
    monkeypatch.setattr(st, "caption", lambda *_: None)
    monkeypatch.setattr(st, "button", lambda *_args, **_kwargs: False)

    login.show_login()
    assert session["user_data"] is expected
    assert session["is_valueable"] is True


class _NullContext:
    """Streamlit 컨테이너 문맥을 대신하는 테스트 객체."""

    def __enter__(self) -> "_NullContext":
        return self

    def __exit__(self, *_args: object) -> None:
        return None
