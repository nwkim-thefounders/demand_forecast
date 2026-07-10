import streamlit as st
import pandas as pd
import snowflake_SQL


# ── 캐시 활성화 버전 ───────────────────────────────────────────────────────────

@st.cache_data(show_spinner=False, ttl=3600)
def _load_product_master_cached() -> pd.DataFrame:
    """PRODUCT_MASTER 테이블 캐시 로드 (TTL 3600초)."""
    return _fetch_product_master()


@st.cache_data(show_spinner=False, ttl=300)
def _load_users_data_cached() -> pd.DataFrame:
    """ALLOWED_USERS 테이블 캐시 로드 (TTL 300초)."""
    return _fetch_users_data()


# ── 실제 Snowflake 조회 로직 ──────────────────────────────────────────────────

def _fetch_product_master() -> pd.DataFrame:
    """PRODUCT_MASTER 테이블에서 품목 정보를 Snowflake에서 직접 조회한다.

    Returns:
        pd.DataFrame: 품목코드, 요청_품목명_국문, 라인, 대분류, 중분류, 용량, 유통코드, 버전 컬럼.

    Raises:
        Exception: Snowflake 연결 또는 쿼리 실행 실패 시.
    """
    engine = snowflake_SQL.connect_snowflake()
    query = (
        'SELECT "품목코드", "요청_품목명_국문", "라인", "대분류", "중분류", '
        '"용량", "유통코드", "버전" FROM TESTDB.PUBLIC.PRODUCT_MASTER;'
    )
    with engine.connect() as conn:
        df = snowflake_SQL.query_to_snowflake_with_text(query=query, conn=conn)
    return df


def _fetch_users_data() -> pd.DataFrame:
    """ALLOWED_USERS 테이블을 Snowflake에서 직접 조회한다.

    Returns:
        pd.DataFrame: EMAIL, USER_NAME, ROLE, USER_PW 등 컬럼 (대문자).

    Raises:
        Exception: Snowflake 연결 또는 쿼리 실행 실패 시.
    """
    engine = snowflake_SQL.connect_snowflake()
    query = "SELECT * FROM TESTDB.PUBLIC.ALLOWED_USERS;"
    with engine.connect() as conn:
        df = snowflake_SQL.query_to_snowflake_with_text(query=query, conn=conn)
        df.columns = [col.upper() for col in df.columns]
    return df


# ── 공개 인터페이스 ───────────────────────────────────────────────────────────

def load_product_master(use_cache: bool = True) -> pd.DataFrame:
    """PRODUCT_MASTER 테이블을 로드한다.

    Args:
        use_cache (bool): True이면 캐시(TTL 3600s)를 사용하고, False이면 매번 새로 조회한다.

    Returns:
        pd.DataFrame: 품목코드, 요청_품목명_국문, 라인, 대분류, 중분류, 용량, 유통코드, 버전 컬럼.

    Raises:
        Exception: Snowflake 연결 또는 쿼리 실행 실패 시.
    """
    if use_cache:
        return _load_product_master_cached()
    return _fetch_product_master()


def clear_users_cache() -> None:
    """ALLOWED_USERS 캐시(_load_users_data_cached)를 초기화한다.

    신규 유저 등록 직후 최신 유저 목록을 다시 조회해야 할 때 호출한다.
    """
    # st.cache_data가 적용된 내부 함수의 캐시를 비움
    _load_users_data_cached.clear()


def load_users_data(use_cache: bool = True) -> pd.DataFrame:
    """ALLOWED_USERS 테이블을 로드하여 로그인 검증에 사용한다.

    Args:
        use_cache (bool): True이면 캐시(TTL 300s)를 사용하고, False이면 매번 새로 조회한다.

    Returns:
        pd.DataFrame: EMAIL, USER_NAME, ROLE, USER_PW 등 컬럼 (대문자).

    Raises:
        Exception: Snowflake 연결 또는 쿼리 실행 실패 시.
    """
    if use_cache:
        return _load_users_data_cached()
    return _fetch_users_data()
