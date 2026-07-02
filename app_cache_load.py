import streamlit as st
import pandas as pd
import snowflake_SQL


@st.cache_data(show_spinner=False, ttl=300)
def load_users_data() -> pd.DataFrame:
    """ALLOWED_USERS 테이블을 로드하여 로그인 검증에 사용한다.

    Returns:
        pd.DataFrame: EMAIL, USER_NAME, ROLE, USER_PW 등 컬럼을 포함한 유저 목록 (컬럼 대문자).

    Raises:
        Exception: Snowflake 연결 또는 쿼리 실행 실패 시.
    """
    engine = snowflake_SQL.connect_snowflake()
    query = "SELECT * FROM TESTDB.PUBLIC.ALLOWED_USERS;"
    with engine.connect() as conn:
        df = snowflake_SQL.query_to_snowflake_with_text(query=query, conn=conn)
        df.columns = [col.upper() for col in df.columns]
    return df
