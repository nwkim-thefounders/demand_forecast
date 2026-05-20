import streamlit as st
import pandas as pd
import app_01_login
import datetime
import snowflake_SQL

check_help_text = """
**검사 로직 설명**
1. SKU 컬럼이 비어있는 행 삭제
2. DESC 컬럼이 비어 있으면 에러 메시지 표시
3. 사업부 컬럼이 비어있으면 에러 메시지 표시
4. 채널 컬럼이 비어있으면 에러 메세지 표시
"""

read_help_text = """
**시트 읽기 로직**
1. QTY 시트를 읽어옵니다.
2. SKU 컬럼이 있는 행부터 시작합니다.
3. SKU 컬럼 이전의 컬럼은 삭제합니다.
4. "카테고리"부터 "FINAL Forecast" 라는 글자가 있는 컬럼까지 삭제합니다.
5. "FINAL Forecast" 컬럼 이후의 컬럼은 삭제합니다.
6. 첫 번째 행을 헤더로 설정합니다.
"""

col_mapping = {
    'SKU': 'SKU',
    'DESC': 'DESC',
    'Status': 'STATUS',
    'ABC class': 'ABC_CLASS',
    '사업부': 'DEPT',
    '채널': 'CHANNEL',
    'FINAL Forecast': 'FINAL_FORECAST'
}

def melt_logic(df):
    df = df.copy()
    id_vars = ['카테고리', 'SKU', 'DESC', 'Status', 'ABC class', '사업부', '채널']
    df = pd.melt(
        df,
        id_vars=id_vars,
        var_name='MONTH',
        value_name="FORECAST_QTY"
    )
    df["SIGNOFF_DT"] = pd.Timestamp.now().strftime("%Y-%m-%d")
    df["FCST_MTH"] = pd.Timestamp.now().strftime("%Y%m")
    df = df.set_index(["SIGNOFF_DT", "FCST_MTH"]).reset_index()
    
    df["FCST_MTH"] = pd.to_numeric(df["FCST_MTH"], errors="coerce")
    df["MONTH"] = pd.to_numeric(df["MONTH"], errors="coerce")
    df["FORECAST_QTY"] = pd.to_numeric(df["FORECAST_QTY"], errors="coerce")
    df["REGISTANT"] = st.session_state.get("user_name_kr", "")

    df = df.drop(columns="카테고리")
    df = df.rename(columns=col_mapping)
    return df

def read_df_xlsx(uploaded_file):
    origin_df = pd.read_excel(uploaded_file, sheet_name="QTY")
    # 모든 데이터 타입을 문자열로 읽기
    # origin_df = origin_df.astype(str)
    df = origin_df.copy()
    for i, row in df.iterrows():
        if "SKU" in row.values:
            df = df.iloc[i:]
            break
    for i, row in df.iterrows():
        if "SKU" in str(row):
            for j, col in enumerate(row):
                if "SKU" in str(col):
                    df = df.drop(df.columns[j-1], axis=1)
                    break
            break
    # origin_df의 "카테고리"부터 "FINAL Forecast" 라는 글자가 있는데 컬럼의 전까지 삭제하는 코드
    # 1 단계 : 행별로 순환 하면서 "카테고리" 글자가 있는 행 찾고, 해당 행에서 "카테고리"라는 글자가 있는 컬럼 인덱스 찾기
    category_col_idx = None
    for i, row in origin_df.iterrows():
        if "카테고리" in str(row.values):
            for j, col in enumerate(row):
                if "카테고리" in str(col):
                    category_col_idx = j
                    break
            break
    
    # 2단계 : "FINAL Forecast" 글자가 있는 행 찾고, 해당 행에서 "FINAL Forecast"라는 글자가 있는 컬럼 인덱스 찾기
    final_forecast_col_idx = None
    sub_header_i = None
    for i, row in origin_df.iterrows():
        if "FINAL Forecast" in str(row.values):
            sub_header_i = i
            for j, col in enumerate(row):
                if "FINAL Forecast" == str(col):
                    final_forecast_col_idx = j-1
                    break
            break
    # 3단계 : sub_header_i 행에서 "M-1" 글자가 있는 행 찾고, 해당 행에서 "M-1"라는 글자가 있는 컬럼 인덱스 찾기
    m1_col_idx = None
    for i, row in origin_df.iterrows():
        if i == sub_header_i:
            for j, col in enumerate(row):
                if j < final_forecast_col_idx + 2:
                    continue
                if type(col) == str: # final_forecast_col_idx 이후에 col의 타입이 str일때 까지
                    m1_col_idx = j-1
                    break
            break

    # 4단계 : m1_col_idx부터 끝까지 삭제
    df = df.drop(df.columns[m1_col_idx:], axis=1) # m1_col_idx 은 76인데 왜 안잘리지?
    # print("df after drop m1_col_idx:", df.shape) # 출력내용: df after drop m1_col_idx: (497, 44)

    # 5단계 : category_col_idx부터 final_forecast_col_idx까지 삭제
    df = df.drop(df.columns[category_col_idx:final_forecast_col_idx], axis=1)

    # 첫 번째 행을 헤더로 설정
    df.columns = df.iloc[0]
    df = df[1:]
    df = df.reset_index(drop=True)
    st.session_state["is_valid"] = True

    # SKU가 비어있는 행 삭제
    df = df.loc[df["SKU"].notna()]

    # desc가 비어있는 행 찾기
    desc_err_df = df.copy()
    desc_err_df = desc_err_df[desc_err_df["DESC"].isna()]
    if not desc_err_df.empty:
        st.session_state["err_msg"] = "QTY 시트의 DESC 컬럼에 빈 값이 있습니다."
        st.session_state["is_valid"] = False
        return df

    # 사업부가 비어있는 행 찾기
    business_unit_err_df = df.copy()
    business_unit_err_df = business_unit_err_df[business_unit_err_df["사업부"].isna()]
    if not business_unit_err_df.empty:
        st.session_state["err_msg"] = "QTY 시트의 사업부 컬럼에 빈 값이 있습니다."
        st.session_state["is_valid"] = False
        return df
    
    # 채널이 비어있는 행 찾기
    channel_err_df = df.copy()
    channel_err_df = channel_err_df[channel_err_df["채널"].isna()]
    if not channel_err_df.empty:
        st.session_state["err_msg"] = "QTY 시트의 채널 컬럼에 빈 값이 있습니다."
        st.session_state["is_valid"] = False
        return df

    st.session_state["is_valid"] = True
    st.session_state["err_msg"] = ""
    df = melt_logic(df)
    st.session_state["df"] = df
    return df

def save_btn():
    engine = snowflake_SQL.connect_snowflake()
    with engine.connect() as conn:
        df = st.session_state.get("df", None)
        if df is not None:
            snowflake_SQL.input_data(conn, df, "MONTH_FORECAST_CONSOL")
    # st.file_uploader에 업로드된 파일 초기화

    st.session_state["df"] = None
    st.session_state["is_valid"] = False
    st.session_state["err_msg"] = ""
    st.session_state["uploader_version"] = st.session_state.get("uploader_version", 0) + 1
    

def show_main():
    st.set_page_config(
        page_title="The Founders IM",
        layout="wide"
    )

    if not st.session_state.get('authentication_status'):
        app_01_login.show_login()
    else:
        if "err_msg" not in st.session_state:
            st.session_state["err_msg"] = ""
            st.session_state["is_valid"] = False
            st.session_state["df"] = None
            st.session_state["uploader_version"] = 0
        main_col1, main_col2, main_col3 = st.columns([0.5, 9, 0.5])
        with main_col2:
            st.title("Demand Forecasting File Upload")
            st.write(f"{st.session_state.get('user_name_kr', '')}님, 환영합니다!")
            st.write("아래 엑셀파일을 업로드 하거나 drag & drop으로 업로드 해주세요.")

            uploaded_file = st.file_uploader(
                label="엑셀 파일 업로드",
                type=["xlsx", "xls"],
                accept_multiple_files=False,
                key=f"upload_excel_{st.session_state.get('uploader_version', 0)}",
            )

            if uploaded_file is not None:
                try:
                    df = read_df_xlsx(uploaded_file)
                    if st.session_state["err_msg"]:
                        st.error(st.session_state["err_msg"])
                    else:
                        if st.session_state["df"] is not None:
                            st.caption("시트 읽어오기", help=read_help_text)
                        st.caption("검사 로직", help=check_help_text)
                        with st.container(border=False, horizontal=True):
                            with st.container(border=False, horizontal=True, horizontal_alignment="left"):
                                st.subheader("데이터 미리보기")
                            with st.container(border=False, horizontal=True, horizontal_alignment="right"):
                                if st.session_state["is_valid"]:
                                    st.button(label="데이터 저장", type="primary", on_click=save_btn)

                        st.dataframe(df, width="stretch")

                except Exception as e:
                    st.error(f"파일을 읽는 중 오류가 발생했습니다: {e}")
            else:
                st.info("업로드된 파일이 없습니다. 업로드할 파일을 선택해주세요.")


show_main()