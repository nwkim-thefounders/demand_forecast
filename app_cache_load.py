import streamlit as st
import snowflake_SQL


@st.cache_data(show_spinner=False)
def load_users_data():
    """ALLOWED_USERS 테이블 로드 (로그인 검증용)"""
    engine = snowflake_SQL.connect_snowflake()
    query = "SELECT * FROM TESTDB.PUBLIC.ALLOWED_USERS;"
    with engine.connect() as conn:
        df = snowflake_SQL.query_to_snowflake_with_text(query=query, conn=conn)
        df.columns = [col.upper() for col in df.columns]
    return df
