import streamlit as st
import snowflake_SQL
from datetime import datetime

this_month_int = int(datetime.now().strftime("%Y%m"))

@st.cache_data(show_spinner=False)
def get_option_df():
    engine = snowflake_SQL.connect_snowflake()
    with engine.connect() as conn:
        df = snowflake_SQL.query_to_snowflake_with_text(conn=conn, query="SELECT DISTINCT FCST_MTH, DEPT, CHANNEL, MONTH, REGISTANT FROM MONTH_FORECAST_CONSOL;")
    
    df.columns = [col.upper() for col in df.columns]

    return df

def init_data():
    df = get_option_df()
    st.session_state["option_df"] = df.copy()
    st.session_state["fcst_month_list"] = sorted(df["FCST_MTH"].drop_duplicates().dropna().tolist())
    st.session_state["target_month_list"] = sorted(df["MONTH"].drop_duplicates().dropna().tolist())
    st.session_state["dept_list"] = sorted(df["DEPT"].drop_duplicates().dropna().tolist())
    st.session_state["channel_list"] = sorted(df["CHANNEL"].drop_duplicates().dropna().tolist())
    st.session_state["registant_list"] = sorted(df["REGISTANT"].drop_duplicates().dropna().tolist())

def show_edit_page():
    if "option_df" not in st.session_state:
        init_data()

    with st.sidebar:
        fcst_month_list = st.session_state.get("fcst_month_list", [])
        st.caption("MONTH_FORECAST_CONSOL 테이블 검색")
        st.select_slider(label="등록 월 - FCST_MTH", options=fcst_month_list, value=(fcst_month_list[-2], fcst_month_list[-1]), key="selectedfcst_month")

        target_month_list = st.session_state.get("target_month_list", [])
        st.select_slider(label="예측 월 - MONTH", options=target_month_list, value=(target_month_list[-2], target_month_list[-1]), key="selected_target_month")

        dept_list = st.session_state.get("dept_list", [])
        st.multiselect(label="사업부 - DEPT", options=dept_list, key="selected_dept")

        channel_list = st.session_state.get("channel_list", [])
        st.multiselect(label="채널 - CHANNEL", options=channel_list, key="selected_channel")

        registant_list = st.session_state.get("registant_list", [])
        st.multiselect(label="등록자 - REGISTANT", options=registant_list, key="selected_registant")

        st.write("")
        st.write("")
        st.write(f"검색할 데이터")
        st.write(f"FCST_MTH : {st.session_state.get("selectedfcst_month")[0]} ~ {st.session_state.get("selectedfcst_month")[1]}")
        st.write(f"MONTH : {st.session_state.get("selected_target_month")[0]} ~ {st.session_state.get("selected_target_month")[1]}")
        st.write(f"DEPT : {', '.join(st.session_state.get("selected_dept", []))}")
        st.write(f"CHANNEL : {', '.join(st.session_state.get("selected_channel", []))}")
        st.write(f"REGISTANT : {', '.join(st.session_state.get("selected_registant", []))}")

        with st.container(border=False, horizontal=False, horizontal_alignment="right"):
            st.write("")
            st.button(label="검색", type="primary")
    
    st.write(st.session_state.get("target_month_list"))