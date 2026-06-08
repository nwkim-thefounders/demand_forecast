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
    try:
        origin_df = pd.read_excel(uploaded_file, sheet_name="QTY")
    except Exception as e:
        st.session_state["err_msg"] = f"엑셀 파일의 'QTY' 시트를 찾을 수 없거나 읽는데 실패했습니다. (원인: {e})"
        st.session_state["is_valid"] = False
        return None

    df = origin_df.copy()
    
    # 1. SKU 행 시작점 찾기
    sku_row_found = False
    for i, row in df.iterrows():
        if "SKU" in row.values:
            df = df.iloc[i:]
            sku_row_found = True
            break
    if not sku_row_found:
        st.session_state["err_msg"] = "시트 내에서 'SKU'가 포함된 시작 행을 찾을 수 없습니다."
        st.session_state["is_valid"] = False
        return None

    for i, row in df.iterrows():
        if "SKU" in str(row):
            for j, col in enumerate(row):
                if "SKU" in str(col):
                    df = df.drop(df.columns[j-1], axis=1)
                    break
            break

    # 2. 카테고리 인덱스 찾기
    category_col_idx = None
    for i, row in origin_df.iterrows():
        # str(row.values) 대신 임의의 원소 중 문자열에 "카테고리"가 포함되어 있는지 리스트 컴프리헨션으로 검사
        if any("카테고리" in str(val) for val in row.values):
            for j, col in enumerate(row):
                if "카테고리" in str(col):
                    category_col_idx = j
                    break
            break
    if category_col_idx == None:
        st.session_state["err_msg"] = "시트에서 '카테고리' 컬럼 위치를 찾을 수 없습니다."
        st.session_state["is_valid"] = False
        return None
    
    # 3. FINAL Forecast 인덱스 찾기
    final_forecast_col_idx = None
    sub_header_i = None
    for i, row in origin_df.iterrows():
        if any("FINAL Forecast" in str(val) for val in row.values):
            sub_header_i = i
            for j, col in enumerate(row):
                if "FINAL Forecast" == str(col).strip(): # 혹시 모를 양끝 공백 제거
                    final_forecast_col_idx = j-1
                    break
            break
        
    if final_forecast_col_idx == None:
        st.session_state["err_msg"] = "시트에서 'FINAL Forecast' 컬럼 위치를 정확히 찾을 수 없습니다."
        st.session_state["is_valid"] = False
        return None

    # 4. M-1 인덱스 찾기
    m1_col_idx = None
    for i, row in origin_df.iterrows():
        if i == sub_header_i:
            for j, col in enumerate(row):
                if j < final_forecast_col_idx + 2:
                    continue
                if type(col) == str: 
                    m1_col_idx = j-1
                    break
            break
    if m1_col_idx == None:
        st.session_state["err_msg"] = "'FINAL Forecast' 이후에 오는 기준 데이터(M-1 등) 컬럼 위치를 찾을 수 없습니다."
        st.session_state["is_valid"] = False
        return None

    # 데이터 자르기 공정
    try:
        # 4단계 : m1_col_idx부터 끝까지 삭제
        df = df.drop(df.columns[m1_col_idx:], axis=1) 
        # 5단계 : category_col_idx부터 final_forecast_col_idx까지 삭제
        df = df.drop(df.columns[category_col_idx:final_forecast_col_idx], axis=1)

        # 첫 번째 행을 헤더로 설정
        df.columns = df.iloc[0]
        df = df[1:]
        df = df.reset_index(drop=True)
    except Exception as e:
        st.session_state["err_msg"] = f"지정된 인덱스로 컬럼을 자르는 중 오류가 발생했습니다: {e}"
        st.session_state["is_valid"] = False
        return None

    # 5. 헤더 변환 후 SKU 컬럼 존재 여부 체크 (🚨 핵심 에러 방지 방어 코드)
    if "SKU" not in df.columns:
        st.session_state["err_msg"] = "데이터 변환 후 'SKU' 컬럼이 헤더에 존재하지 않습니다. 엑셀 파일 형식을 확인해주세요."
        st.session_state["is_valid"] = False
        return None

    # SKU가 비어있는 행 삭제
    df = df.loc[df["SKU"].notna()]

    # desc가 비어있는 행 찾기
    if "DESC" not in df.columns:
        st.session_state["err_msg"] = "'DESC' 컬럼을 찾을 수 없습니다."
        st.session_state["is_valid"] = False
        return None
        
    desc_err_df = df[df["DESC"].isna()]
    if not desc_err_df.empty:
        st.session_state["err_msg"] = "QTY 시트의 DESC 컬럼에 빈 값이 있습니다."
        st.session_state["is_valid"] = False
        return df

    # 사업부가 비어있는 행 찾기
    if "사업부" not in df.columns:
        st.session_state["err_msg"] = "'사업부' 컬럼을 찾을 수 없습니다."
        st.session_state["is_valid"] = False
        return None

    business_unit_err_df = df[df["사업부"].isna()]
    if not business_unit_err_df.empty:
        st.session_state["err_msg"] = "QTY 시트의 사업부 컬럼에 빈 값이 있습니다."
        st.session_state["is_valid"] = False
        return df
    
    # 채널이 비어있는 행 찾기
    if "채널" not in df.columns:
        st.session_state["err_msg"] = "'채널' 컬럼을 찾을 수 없습니다."
        st.session_state["is_valid"] = False
        return None

    channel_err_df = df[df["채널"].isna()]
    if not channel_err_df.empty:
        st.session_state["err_msg"] = "QTY 시트의 채널 컬럼에 빈 값이 있습니다."
        st.session_state["is_valid"] = False
        return df

    st.session_state["is_valid"] = True
    st.session_state["err_msg"] = ""
    
    try:
        df = melt_logic(df)
    except Exception as e:
        st.session_state["err_msg"] = f"데이터 구조 변경(Melt) 중 오류가 발생했습니다: {e}"
        st.session_state["is_valid"] = False
        return None

    st.session_state["df"] = df
    return df

def save_btn():
    with st.spinner("데이터를 저장 중입니다..."):
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
                    
                    # 에러 메시지가 세션에 담겨 있다면 에러박스 출력
                    if st.session_state.get("err_msg"):
                        st.error(st.session_state["err_msg"])
                    elif df is not None:
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
                    # 예상치 못한 시스템 치명적 에러 핸들링
                    st.error(f"시스템 예외가 발생했습니다 (개발자 문의 필요): {e}")
            else:
                st.info("업로드된 파일이 없습니다. 업로드할 파일을 선택해주세요.")


show_main()