"""ALLOWED_USERS 접속 위치(CUTOVER) 설정 회귀 테스트.

Snowflake 접속 없이(오프라인) 위치 설정·화이트리스트·읽기/쓰기 공유 여부를 검증한다.
"""

import importlib
import sys
from typing import Any

import pytest
import streamlit as st

import app_cache_load
import snowflake_SQL

LEGACY_FQN = "TESTDB.PUBLIC.ALLOWED_USERS"
NEW_FQN = "DATA_DB.ADMIN.ALLOWED_USERS"


@pytest.fixture(autouse=True)
def _clean_location_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """각 테스트 시작 시 위치 설정 환경 변수를 제거한다."""
    monkeypatch.delenv(snowflake_SQL.ALLOWED_USERS_FQN_KEY, raising=False)
    # st.secrets 접근이 실제 secrets.toml을 읽지 않도록 빈 dict로 대체한다.
    monkeypatch.setattr(st, "secrets", {})


def test_default_is_legacy_location() -> None:
    """설정이 없으면 현재 위치(TESTDB.PUBLIC)를 반환한다."""
    assert snowflake_SQL.get_allowed_users_fqn() == LEGACY_FQN


def test_env_overrides_to_new_location(monkeypatch: pytest.MonkeyPatch) -> None:
    """환경 변수 값이 신규 위치면 그대로 반환한다(대소문자·공백 정규화)."""
    monkeypatch.setenv(snowflake_SQL.ALLOWED_USERS_FQN_KEY, " data_db.admin.allowed_users ")
    assert snowflake_SQL.get_allowed_users_fqn() == NEW_FQN


def test_secrets_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    """환경 변수가 없으면 st.secrets 값을 사용한다."""
    monkeypatch.setattr(st, "secrets", {snowflake_SQL.ALLOWED_USERS_FQN_KEY: NEW_FQN})
    assert snowflake_SQL.get_allowed_users_fqn() == NEW_FQN


def test_empty_env_falls_back_to_secrets(monkeypatch: pytest.MonkeyPatch) -> None:
    """빈 환경 변수 값이면 secrets 설정을 사용한다."""
    monkeypatch.setenv(snowflake_SQL.ALLOWED_USERS_FQN_KEY, "")
    monkeypatch.setattr(st, "secrets", {snowflake_SQL.ALLOWED_USERS_FQN_KEY: NEW_FQN})
    assert snowflake_SQL.get_allowed_users_fqn() == NEW_FQN


def test_missing_secrets_file_uses_default(monkeypatch: pytest.MonkeyPatch) -> None:
    """secrets 파일이 없는 실행 환경에서는 기존 위치 기본값을 쓴다."""

    class _MissingSecrets:
        def get(self, key: str) -> None:
            raise FileNotFoundError(key)

    monkeypatch.setattr(st, "secrets", _MissingSecrets())
    assert snowflake_SQL.get_allowed_users_fqn() == LEGACY_FQN


@pytest.mark.parametrize(
    "bad_value",
    [
        "TESTDB.PUBLIC.ALLOWED_USERS; DROP TABLE X",
        "OTHER_DB.PUBLIC.ALLOWED_USERS",
        "ALLOWED_USERS",
        '"DATA_DB"."ADMIN"."ALLOWED_USERS"',
    ],
)
def test_non_whitelisted_value_is_rejected(
    monkeypatch: pytest.MonkeyPatch, bad_value: str
) -> None:
    """화이트리스트 밖 값은 SQL에 넣지 않고 ValueError를 발생시킨다."""
    monkeypatch.setenv(snowflake_SQL.ALLOWED_USERS_FQN_KEY, bad_value)
    with pytest.raises(ValueError):
        snowflake_SQL.get_allowed_users_fqn()


def test_read_query_uses_configured_location(monkeypatch: pytest.MonkeyPatch) -> None:
    """읽기(_fetch_users_data)가 설정된 위치로 SELECT 한다."""
    captured: dict[str, Any] = {}

    class _FakeConn:
        def __enter__(self) -> "_FakeConn":
            return self

        def __exit__(self, *args: object) -> None:
            return None

    class _FakeEngine:
        def connect(self) -> _FakeConn:
            return _FakeConn()

    import pandas as pd

    def _fake_query(query: str, conn: object) -> pd.DataFrame:
        captured["query"] = query
        return pd.DataFrame({"email": ["a"]})

    monkeypatch.setattr(snowflake_SQL, "connect_snowflake", lambda: _FakeEngine())
    monkeypatch.setattr(snowflake_SQL, "query_to_snowflake_with_text", _fake_query)

    app_cache_load._fetch_users_data()
    assert LEGACY_FQN in captured["query"]

    monkeypatch.setenv(snowflake_SQL.ALLOWED_USERS_FQN_KEY, NEW_FQN)
    app_cache_load._fetch_users_data()
    assert NEW_FQN in captured["query"]
    assert LEGACY_FQN not in captured["query"]


def _import_login(monkeypatch: pytest.MonkeyPatch) -> Any:
    """가짜 secrets로 app_01_login을 임포트한다(실제 secrets.toml 미사용)."""
    fake_secrets = {
        "slack": {"client_id": "x", "client_secret": "x", "redirect_uri": "http://localhost"},
    }
    monkeypatch.setattr(st, "secrets", fake_secrets)
    monkeypatch.delitem(sys.modules, "app_01_login", raising=False)
    module = importlib.import_module("app_01_login")
    # 테스트 종료 시 모듈 캐시를 정리한다.
    monkeypatch.setitem(sys.modules, "app_01_login", module)
    return module


def test_write_query_uses_configured_location(monkeypatch: pytest.MonkeyPatch) -> None:
    """쓰기(regist_user)가 설정된 위치로 INSERT 하고 값은 바인드 파라미터로 전달한다."""
    login = _import_login(monkeypatch)
    executed: list[tuple[str, dict[str, Any]]] = []

    class _FakeConn:
        def __enter__(self) -> "_FakeConn":
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def execute(self, stmt: object, params: dict[str, Any]) -> None:
            executed.append((str(stmt), params))

        def commit(self) -> None:
            return None

        def rollback(self) -> None:
            return None

    class _FakeEngine:
        def connect(self) -> _FakeConn:
            return _FakeConn()

    monkeypatch.setattr(login.snowflake_SQL, "connect_snowflake", lambda: _FakeEngine())

    login.regist_user(email="a@example.com", name="n")
    assert f"INSERT INTO {LEGACY_FQN} " in executed[-1][0]
    assert ":email" in executed[-1][0]

    monkeypatch.setenv(snowflake_SQL.ALLOWED_USERS_FQN_KEY, NEW_FQN)
    login.regist_user(email="a@example.com", name="n")
    assert f"INSERT INTO {NEW_FQN} " in executed[-1][0]
    assert executed[-1][1]["email"] == "a@example.com"


def test_write_failure_rolls_back_and_propagates(monkeypatch: pytest.MonkeyPatch) -> None:
    """INSERT 오류는 rollback 후 호출자에게 전파한다."""
    login = _import_login(monkeypatch)
    events: list[str] = []

    class _FakeConn:
        def __enter__(self) -> "_FakeConn":
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def execute(self, stmt: object, params: dict[str, Any]) -> None:
            events.append("execute")
            raise ValueError("insert failed")

        def commit(self) -> None:
            events.append("commit")

        def rollback(self) -> None:
            events.append("rollback")

    class _FakeEngine:
        def connect(self) -> _FakeConn:
            return _FakeConn()

    monkeypatch.setattr(login.snowflake_SQL, "connect_snowflake", lambda: _FakeEngine())
    with pytest.raises(ValueError, match="insert failed"):
        login.regist_user(email="a@example.com", name="n")
    assert events == ["execute", "rollback"]
