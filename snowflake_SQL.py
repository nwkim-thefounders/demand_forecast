from sqlalchemy import create_engine
from sqlalchemy import text
from snowflake.sqlalchemy import URL
from snowflake.connector.pandas_tools import pd_writer
from cryptography.hazmat.primitives import serialization
from datetime import timedelta
import pandas as pd
import time
import streamlit as st


def connect_snowflake():
    key = st.secrets["snowflake"]["key"]

    p_key = serialization.load_pem_private_key(
        key.encode(),
        password=None
    )

    pkb = p_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    engine = create_engine(URL(
        account='OLQVRGS-BM97392',
        user='NW.KIM',
        warehouse='COMPUTE_WH',
        database='TESTDB',
        schema='PUBLIC',
    ), connect_args={
        'private_key': pkb,
    })

    return engine


def input_data(conn, df: pd.DataFrame, table_name: str):
    print(f'{table_name}에 데이터 입력중...')
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
        print(e)
        
    end_time = time.time()
    elapsed_time = timedelta(seconds=end_time - start_time)
    print(f'{table_name}에 데이터 입력 완료... {elapsed_time}\n')


def query_to_snowflake_with_text(query, conn):
    df = pd.read_sql(text(query), conn)
    conn.commit()
    return df
