import streamlit as st
import pandas as pd
from sqlalchemy import text
from concurrent.futures import ThreadPoolExecutor, as_completed

import snowflake_SQL

def _get_dataframe_from_snowflake(table_name:str, snap_date: str = None):
    if snap_date is None:
        query = f"SELECT * FROM TESTDB.PUBLIC.{table_name} WHERE SNAP_DATE = (SELECT MAX(SNAP_DATE) FROM {table_name})"
    else:
        query = f"SELECT * FROM TESTDB.PUBLIC.{table_name} WHERE SNAP_DATE = '{snap_date}';"

    engine = snowflake_SQL.connect_snowflake()
    with engine.connect() as conn:
        df = pd.read_sql(text(query), conn)
        if not df.empty:
            df.columns = [col.upper() for col in df.columns]

    result_df = df if not df.empty else pd.DataFrame()
    return table_name, result_df

def _init_data():
    engine = snowflake_SQL.connect_snowflake()
    with engine.connect() as conn:
        query = "SELECT * FROM TABLE_INFO"
        table_info_df = pd.read_sql(text(query), conn)
        st.session_state["table_info_df"] = table_info_df
    
    table_list = table_info_df["table_name"].drop_duplicates().to_list()
    with ThreadPoolExecutor(max_workers=len(table_list)) as executor:
        futures = {executor.submit(_get_dataframe_from_snowflake, table_name, None): table_name for table_name in table_list}

        stock_list = []
        for future in as_completed(futures):
            table_name = futures[future]
            try:
                tbl_name, df = future.result()
                data = {
                    "table_name": tbl_name,
                    "dataframe": df
                }
                stock_list.append(data)
            except Exception as e:
                print(e)
                st.session_state[table_name] = pd.DataFrame()
        st.session_state["stock_list"] = stock_list


def _render_search():
    st.subheader("검색")
    with st.expander(label="검색 설정", expanded=True):
        st.text_input(label="input")

def show_stock_view():
    _render_search()
    if "stock_list" not in st.session_state:
        _init_data()

    stock_list = st.session_state["stock_list"]
    for stock_dict in stock_list:
        table_name = stock_dict["table_name"]
        df = stock_dict["dataframe"]

        st.write(table_name)
        st.dataframe(df)