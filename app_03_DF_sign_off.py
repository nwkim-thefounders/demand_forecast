import streamlit as st
import snowflake_SQL
import pandas as pd

HOW_TO_USE = """
Sign Off로 변경을 원하는 데이터의 체크 박스를 체크 후 저장 버튼 클릭하면 해당 데이터가 Sign Off 상태로 변경 됩니다.\n
단, 선택한 값의 (FCST_MTH, DEPT, CHANNEL)이 같은 기존 Sign Off 데이터는 Regist로 전환 됩니다.\n
초록색 표기된 행은 SIGNOFF_DT가 가장 최신인 행 입니다..
"""

def show_sign_off():
    if st.session_state.get("user_role") != "ADMIN":
        st.warning("해당 페이지는 ADMIN 계정만 접근 가능합니다.")
        return
    
    st.title("Sign Off")
    st.caption("업로드된 데이터를 조회하고 Sign Off 처리를 위한 페이지 입니다.")
    st.write("")
    
    # 시작 데이터 없으면 _init_data() 실행
    if "fcst_data" not in st.session_state:
        _init_data()

    # vertical_alignment="bottom" 으로 수평 및 수직 하단 정렬
    col0, col1, col2, col3, col4 = st.columns([0.7, 0.7, 0.7, 0.7, 0.7], vertical_alignment="bottom")

    with col0:
        fcst_month_list = st.session_state.get("fcst_month_list", [])
        st.selectbox(
            label="등록 월 - FCST_MTH", 
            options=fcst_month_list,
            key="fcst_month_search",
            index=None,
            placeholder="등록 월을 선택하세요",
            on_change=_flexible_select
        )

    with col1:
        fcst_dept_list = st.session_state.get("fcst_dept_list", [])
        st.multiselect(
            label="사업부 - DEPT",
            options=fcst_dept_list,
            key="fcst_dept_search",
            default=[],
            placeholder="사업부를 선택하세요",
            on_change=_flexible_select
        )

    with col2:
        fcst_channel_list = st.session_state.get("fcst_channel_list", [])
        st.multiselect(
            label="채널 - CHANNEL",
            options=fcst_channel_list,
            key="fcst_channel_search",
            default=[],
            placeholder="채널을 선택하세요",
            on_change=_flexible_select
        )

    with col3:
        fcst_sign_status_list = st.session_state.get("fcst_sign_status_list", [])
        st.selectbox(
            label="상태 - SIGN STATUS",
            options=fcst_sign_status_list,
            key="fcst_sign_status_search",
            index=None,
            placeholder="상태를 선택하세요",
            on_change=_flexible_select
        )
    
    with col4:
        registant_list = st.session_state.get("registant_list", [])
        st.selectbox(
            label="담당자 - REGIANT",
            options=registant_list,
            key="registant_search",
            index=None,
            placeholder="담당자를 선택하세요",
            on_change=_flexible_select
        )

    # '설명'과 메세지 영역을 같은 줄에 배치 (메세지 유무와 무관하게 고정 높이로 자리를 미리 확보)
    desc_col, msg_col = st.columns([0.7, 3], vertical_alignment="center")
    with desc_col:
        st.markdown(body="**설명**", help=HOW_TO_USE)
    with msg_col:
        with st.container(border=False, height=60):
            if st.session_state.get("message", None):
                with st.container(border=False, horizontal=True):
                    st.warning(st.session_state["message"])
                    st.button("**x**", on_click=_delete_message, type="tertiary")
    st.write("")
    # 선택 필터 조건에 맞춰 데이터프레임 파싱 후 표시
    df = _parsing_df(st.session_state["fcst_data"])
    styled_df = df.style.apply(_highlight_latest_signoff, axis=None)
    act_df = st.data_editor(
        styled_df,
        hide_index=True,
        width="stretch",
        # '선택' 컬럼을 제외한 나머지는 수정 불가(읽기 전용) 처리
        disabled=[col for col in df.columns if col != "선택"],
        column_config={
            "선택": st.column_config.CheckboxColumn(
                "선택",
                default=False,
            )
        },
        key="sign_off_editor"
    )

    st.session_state["act_df"] = act_df

    with st.container(border=False, horizontal=True, horizontal_alignment="right"):
        st.button(label="**Sign Off**", key="save_btn", on_click=_on_click_save_btn)

def _on_click_save_btn():
    df = st.session_state.get("act_df").copy()

    # 선택된 행 추출
    checked_df = df.loc[df["선택"] == True].copy()

    # 키값 설정
    df["KEY"] = df["FCST_MTH"].astype(str) + df["DEPT"].astype(str) + df["CHANNEL"].astype(str)
    checked_df["KEY"] = checked_df["FCST_MTH"].astype(str) + checked_df["DEPT"].astype(str) + checked_df["CHANNEL"].astype(str)

    # 방어코드0: 선택한 값이 없는 경우
    if checked_df.empty:
        st.session_state["message"] = "선택된 행이 없습니다."
        return

    # 방어코드1: 선택한 값의 SIGN_STATUS가 이미 SIGNOFF인 경우
    already_signoff_df = checked_df.loc[checked_df["SIGN_STATUS"] == "SIGNOFF"]
    if not already_signoff_df.empty:
        already_sign_channel_list = already_signoff_df["CHANNEL"].drop_duplicates().tolist()
        st.session_state["message"] = f"선택한 행 중 SIGN_STATUS가 이미 SIGNOFF인 행이 포함되어 있습니다.\n\nSIGNOFF 채널: **{', '.join(already_sign_channel_list)}**"
        return

    # 방어코드2: 선택한 여러 행중 같은 키값이 있는지 검사
    duple_checked_df = checked_df.copy()
    duple_checked_df["COUNT_KEY"] = duple_checked_df.groupby("KEY")["KEY"].transform("count")
    if not duple_checked_df.loc[duple_checked_df["COUNT_KEY"] > 1].empty:
        duple_channel_list = duple_checked_df["CHANNEL"].drop_duplicates().tolist()
        st.session_state["message"] = f"선택한 행 중 FCST_MTH, DEPT, CHANNEL이 중복인 행이 있습니다. 중복없이 선택 해주세요\n\n중복 채널: **{', '.join(duple_channel_list)}**"
        return

    # 기존 signoff 상태 대상 검색
    df = pd.merge(
        left=df,
        right=checked_df[["KEY"]].drop_duplicates(),
        on="KEY",
        how="inner" # inner join으로 간결화
    )
    df_signoff = df.loc[df["SIGN_STATUS"] == "SIGNOFF"].copy()

    # 반복문 시작 전에 전부 문자열로 변환
    df_signoff = df_signoff.astype(str)
    checked_df = checked_df.astype(str)

    with st.spinner("DB 반영 중..."):
        engine = snowflake_SQL.connect_snowflake()
        with engine.connect() as conn:
            # 1) 기존 SIGNOFF -> REGIST 로 변경
            if not df_signoff.empty:
                for _, row in df_signoff.iterrows():
                    regist_update_query = f"""
                    UPDATE TESTDB.PUBLIC.MONTH_FORECAST_CONSOL
                    SET
                        "SIGN_STATUS" = 'REGIST'
                    WHERE
                        "SIGNOFF_DT" = '{row["SIGNOFF_DT"]}'
                        AND "FCST_MTH" = '{row["FCST_MTH"]}'
                        AND "DEPT" = '{row["DEPT"]}'
                        AND "CHANNEL" = '{row["CHANNEL"]}'
                        AND "REGISTANT" = '{row["REGISTANT"]}'
                        AND "SIGN_STATUS" = '{row["SIGN_STATUS"]}';
                    """
                    snowflake_SQL.query_to_snowflake_with_text(query=regist_update_query, conn=conn)

            # 2) 선택된 데이터 -> SIGNOFF 로 변경
            for _, row in checked_df.iterrows():
                signoff_update_query = f"""
                UPDATE TESTDB.PUBLIC.MONTH_FORECAST_CONSOL
                SET
                    "SIGN_STATUS" = 'SIGNOFF'
                WHERE
                    "SIGNOFF_DT" = '{row["SIGNOFF_DT"]}'
                    AND "FCST_MTH" = '{row["FCST_MTH"]}'
                    AND "DEPT" = '{row["DEPT"]}'
                    AND "CHANNEL" = '{row["CHANNEL"]}'
                    AND "REGISTANT" = '{row["REGISTANT"]}'
                    AND "SIGN_STATUS" = '{row["SIGN_STATUS"]}';
                """
                snowflake_SQL.query_to_snowflake_with_text(query=signoff_update_query, conn=conn)

            # DB 저장 트랜잭션 수동 커밋
            conn.commit()

        # 데이터 초기화 및 상태 갱신
        _init_data()
        
        # st.data_editor 가 세션 값을 바라보게 하기 위해 위젯 key 초기화
        if "sign_off_editor" in st.session_state:
            del st.session_state["sign_off_editor"]
            
        st.session_state["message"] = "Sign Off 처리가 성공적으로 완료되었습니다."

def _delete_message():
    st.session_state["message"] = None

def _highlight_latest_signoff(df: pd.DataFrame):
    if df.empty:
        return df

    # 데이터프레임 복사 및 날짜 컬럼 타입 변환 (정확한 비교를 위해)
    temp_df = df.copy()
    temp_df['SIGNOFF_DT_TEMP'] = pd.to_datetime(temp_df['SIGNOFF_DT'], errors='coerce')

    # FCST_MTH, DEPT, CHANNEL 별로 가장 최신(max) SIGNOFF_DT 찾기
    latest_dt = temp_df.groupby(['FCST_MTH', 'DEPT', 'CHANNEL'])['SIGNOFF_DT_TEMP'].transform('max')

    # 최신 날짜와 일치하는 행 위치(Boolean Mask) 생성 (날짜 값이 존재하는 경우만)
    is_latest = (temp_df['SIGNOFF_DT_TEMP'] == latest_dt) & temp_df['SIGNOFF_DT_TEMP'].notna()

    # 스타일을 지정할 빈 DataFrame 생성 (기존 df와 동일한 형태)
    style_df = pd.DataFrame('', index=df.index, columns=df.columns)

    # 1. '행 전체'에 초록색 하이라이트를 주고 싶은 경우
    style_df[is_latest] = 'background-color: #d4edda; color: #155724; font-weight: bold;'

    # 2. 만약 'SIGNOFF_DT' 컬럼에만 강조를 주고 싶다면 아래 주석을 해제하세요.
    # style_df.loc[is_latest, 'SIGNOFF_DT'] = 'background-color: #d4edda; color: #155724; font-weight: bold;'

    return style_df

def _flexible_select():
    # 선택된 값 가져오기 (None 이면 빈 문자열)
    fcst_month_search = st.session_state.get("fcst_month_search") or ""
    fcst_dept_search = st.session_state.get("fcst_dept_search") or []
    fcst_channel_search = st.session_state.get("fcst_channel_search") or []
    fcst_sign_status_search = st.session_state.get("fcst_sign_status_search") or ""  # 변수명 수정
    registant_search = st.session_state.get("registant_search") or ""  # 변수명 수정

    df = st.session_state["fcst_data"].copy()
    
    # astype(str)을 거쳐 에러 방지 및 부분 검색(contains) 수행
    # DEPT, CHANNEL은 다중 선택이므로 선택된 목록이 있을 때만 isin으로 필터링
    df = df.loc[
        (df["FCST_MTH"].astype(str).str.contains(str(fcst_month_search))) &
        (df["DEPT"].astype(str).isin(fcst_dept_search) if fcst_dept_search else True) &
        (df["CHANNEL"].astype(str).isin(fcst_channel_search) if fcst_channel_search else True) &
        (df["SIGN_STATUS"].astype(str).str.contains(str(fcst_sign_status_search))) &
        (df["REGISTANT"].astype(str).str.contains(str(registant_search)))
    ]

    # 드롭다운 옵션 목록(List) 업데이트
    st.session_state["fcst_month_list"] = sorted(df["FCST_MTH"].dropna().astype(str).unique().tolist())
    st.session_state["fcst_dept_list"] = sorted(df["DEPT"].dropna().astype(str).unique().tolist())
    st.session_state["fcst_channel_list"] = sorted(df["CHANNEL"].dropna().astype(str).unique().tolist())
    st.session_state["fcst_sign_status_list"] = sorted(df["SIGN_STATUS"].dropna().astype(str).unique().tolist())
    st.session_state["registant_list"] = sorted(df["REGISTANT"].dropna().astype(str).unique().tolist())

def _parsing_df(df: pd.DataFrame):
    fcst_month_search = st.session_state.get("fcst_month_search")
    fcst_dept_search = st.session_state.get("fcst_dept_search")
    fcst_channel_search = st.session_state.get("fcst_channel_search")
    fcst_sign_status_search = st.session_state.get("fcst_sign_status_search")
    registant_search = st.session_state.get("registant_search")

    # 선택된 값이 있을 때만 필터링 진행
    if fcst_month_search:
        df = df.loc[df["FCST_MTH"].astype(str) == str(fcst_month_search)]

    if fcst_dept_search:
        df = df.loc[df["DEPT"].astype(str).isin(fcst_dept_search)]

    if fcst_channel_search:
        df = df.loc[df["CHANNEL"].astype(str).isin(fcst_channel_search)]

    if fcst_sign_status_search:
        df = df.loc[df["SIGN_STATUS"].astype(str) == str(fcst_sign_status_search)]

    if registant_search:
        df = df.loc[df["REGISTANT"].astype(str) == str(registant_search)]

    if not "선택" in df.columns:
        df.insert(0, "선택", False)

    return df

def _init_data():
    engine = snowflake_SQL.connect_snowflake()
    with engine.connect() as conn:
        df = snowflake_SQL.query_to_snowflake_with_text(
            conn=conn,
            query="SELECT DISTINCT SIGNOFF_DT, FCST_MTH, DEPT, CHANNEL, REGISTANT, SIGN_STATUS FROM TESTDB.PUBLIC.MONTH_FORECAST_CONSOL;"
        )
    df.columns = [col.upper() for col in df.columns]

    # 불러온 초기 데이터 컬럼들을 문자열로 형변환 처리
    df["FCST_MTH"] = df["FCST_MTH"].dropna().astype(str).str.replace(".0", "", regex=False)
    df["DEPT"] = df["DEPT"].fillna("").astype(str)
    df["CHANNEL"] = df["CHANNEL"].fillna("").astype(str)
    df["SIGN_STATUS"] = df["SIGN_STATUS"].fillna("").astype(str)

    st.session_state["fcst_data"] = df
    
    # dropna().unique() 후 정렬하여 float 타입 혼입 방지
    st.session_state["fcst_month_list"] = sorted(df["FCST_MTH"].astype("str").replace("", None).dropna().unique().tolist())
    st.session_state["fcst_dept_list"] = sorted(df["DEPT"].astype("str").replace("", None).dropna().unique().tolist())
    st.session_state["fcst_channel_list"] = sorted(df["CHANNEL"].astype("str").replace("", None).dropna().unique().tolist())
    st.session_state["fcst_sign_status_list"] = sorted(df["SIGN_STATUS"].astype("str").replace("", None).dropna().unique().tolist())
    st.session_state["registant_list"] = sorted(df["REGISTANT"].astype("str").replace("", None).dropna().unique().tolist())

    st.session_state["message"] = None