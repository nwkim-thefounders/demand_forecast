from sqlalchemy import create_engine, text, Engine
from sqlalchemy.engine import Connection
from snowflake.sqlalchemy import URL
from snowflake.connector.pandas_tools import pd_writer
from cryptography.hazmat.primitives import serialization
from datetime import timedelta
import logging
import pandas as pd
import time
import streamlit as st

logger = logging.getLogger(__name__)


def connect_snowflake() -> Engine:
    """st.secrets에서 PEM 개인키와 접속 정보를 읽어 Snowflake SQLAlchemy 엔진을 생성한다.

    Returns:
        Engine: Snowflake에 연결된 SQLAlchemy Engine 객체.

    Raises:
        KeyError: st.secrets에 필수 키가 없을 때.
        ValueError: PEM 키 파싱 실패 시.
    """
    key = st.secrets["snowflake"]["key"]

    p_key = serialization.load_pem_private_key(
        key.strip().encode(),
        password=None
    )

    pkb = p_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    sf = st.secrets["snowflake"]
    engine = create_engine(URL(
        account=sf["account"],
        user=sf["user"],
        warehouse=sf["warehouse"],
        database=sf["database"],
        schema=sf["schema"],
    ), connect_args={
        'private_key': pkb,
    })

    return engine


def input_data(conn: Connection, df: pd.DataFrame, table_name: str) -> None:
    """DataFrame을 Snowflake 테이블에 APPEND 방식으로 INSERT한다.

    Args:
        conn (Connection): 활성화된 SQLAlchemy Connection 객체.
        df (pd.DataFrame): 저장할 데이터.
        table_name (str): 대상 테이블명 (자동으로 대문자 변환됨).

    Raises:
        Exception: 데이터 INSERT 또는 commit 실패 시.
    """
    logger.info("%s에 데이터 입력중...", table_name)
    start_time = time.time()

    df.to_sql(
        table_name.upper(),
        conn,
        index=False,
        if_exists='append',
        method=pd_writer   # 속도를 위해 멀티 인서트를 사용합니다.
    )

    try:
        conn.commit()
    except Exception as e:
        logger.error("%s commit 실패: %s", table_name, e)

    end_time = time.time()
    elapsed_time = timedelta(seconds=end_time - start_time)
    logger.info("%s에 데이터 입력 완료... %s", table_name, elapsed_time)


def query_to_snowflake_with_text(query: str, conn: Connection) -> pd.DataFrame:
    """텍스트 SQL 쿼리를 실행하고 결과를 DataFrame으로 반환한다.

    Args:
        query (str): 실행할 SQL 쿼리 문자열.
        conn (Connection): 활성화된 SQLAlchemy Connection 객체.

    Returns:
        pd.DataFrame: 쿼리 결과 DataFrame.

    Raises:
        Exception: 쿼리 실행 실패 시.
    """
    df = pd.read_sql(text(query), conn)
    return df
