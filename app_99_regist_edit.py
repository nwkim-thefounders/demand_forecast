import streamlit as st
import snowflake_SQL
import app_cache_load
import pandas as pd
import logging
import plotly.graph_objects as go
from typing import Optional

logger = logging.getLogger(__name__)


@st.cache_data(show_spinner=False, ttl=600)
def _get_option_df_cached() -> pd.DataFrame:
    """필터 옵션 데이터 캐시 로드 (TTL 600초)."""
    return _fetch_option_df()


def _fetch_option_df() -> pd.DataFrame:
    """MONTH_FORECAST_CONSOL 테이블에서 필터 옵션용 distinct 데이터를 직접 조회한다.

    Returns:
        pd.DataFrame: FCST_MTH, DEPT, CHANNEL, MONTH, REGISTANT distinct 목록.

    Raises:
        Exception: Snowflake 연결 또는 쿼리 실행 실패 시.
    """
    engine = snowflake_SQL.connect_snowflake()
    with engine.connect() as conn:
        df = snowflake_SQL.query_to_snowflake_with_text(
            conn=conn,
            query="SELECT DISTINCT FCST_MTH, DEPT, CHANNEL, MONTH, REGISTANT FROM TESTDB.PUBLIC.MONTH_FORECAST_CONSOL;"
        )
    df.columns = [col.upper() for col in df.columns]
    return df


def get_option_df(use_cache: bool = True) -> pd.DataFrame:
    """MONTH_FORECAST_CONSOL 테이블에서 필터 옵션용 distinct 데이터를 조회한다.

    Args:
        use_cache (bool): True이면 캐시(TTL 600s)를 사용하고, False이면 매번 새로 조회한다.

    Returns:
        pd.DataFrame: FCST_MTH, DEPT, CHANNEL, MONTH, REGISTANT distinct 목록.

    Raises:
        Exception: Snowflake 연결 또는 쿼리 실행 실패 시.
    """
    if use_cache:
        return _get_option_df_cached()
    return _fetch_option_df()


def init_data() -> None:
    """세션 상태에 필터 옵션 목록을 초기화한다."""
    use_cache = st.session_state.get("use_option_cache", True)
    df = get_option_df(use_cache=use_cache)
    st.session_state["option_df"] = df.copy()
    st.session_state["fcst_month_list"] = sorted(df["FCST_MTH"].drop_duplicates().dropna().tolist())
    st.session_state["target_month_list"] = sorted(df["MONTH"].drop_duplicates().dropna().tolist())
    st.session_state["dept_list"] = sorted(df["DEPT"].drop_duplicates().dropna().tolist())
    st.session_state["channel_list"] = sorted(df["CHANNEL"].drop_duplicates().dropna().tolist())
    st.session_state["registant_list"] = sorted(df["REGISTANT"].drop_duplicates().dropna().tolist())


def search_data() -> None:
    """사이드바 필터 조건으로 Snowflake 데이터를 조회하여 세션에 저장한다."""
    fcst_range = st.session_state.get("selectedfcst_month", (None, None))
    target_range = st.session_state.get("selected_target_month", (None, None))
    selected_dept = st.session_state.get("selected_dept", [])
    selected_channel = st.session_state.get("selected_channel", [])
    selected_registant = st.session_state.get("selected_registant", [])

    # WHERE 절 조건 조립
    conditions = []
    if fcst_range[0] and fcst_range[1]:
        conditions.append(f"FCST_MTH BETWEEN {fcst_range[0]} AND {fcst_range[1]}")
    if target_range[0] and target_range[1]:
        conditions.append(f"MONTH BETWEEN {target_range[0]} AND {target_range[1]}")
    if selected_dept:
        dept_list_str = ", ".join([f"'{d}'" for d in selected_dept])
        conditions.append(f"DEPT IN ({dept_list_str})")
    if selected_channel:
        ch_list_str = ", ".join([f"'{c}'" for c in selected_channel])
        conditions.append(f"CHANNEL IN ({ch_list_str})")
    if selected_registant:
        reg_list_str = ", ".join([f"'{r}'" for r in selected_registant])
        conditions.append(f"REGISTANT IN ({reg_list_str})")

    where_clause = " AND ".join(conditions) if conditions else "1=1"
    query = f"SELECT * FROM TESTDB.PUBLIC.MONTH_FORECAST_CONSOL WHERE {where_clause};"

    with st.spinner("데이터 조회 중..."):
        try:
            engine = snowflake_SQL.connect_snowflake()
            with engine.connect() as conn:
                result_df = snowflake_SQL.query_to_snowflake_with_text(query=query, conn=conn)
            result_df.columns = [col.upper() for col in result_df.columns]
            result_df = _result_df_edit(result_df)
            use_product_cache = st.session_state.get("use_product_cache", True)
            with st.spinner("품목 마스터 병합 중..."):
                result_df = _merge_product_master(result_df, use_cache=use_product_cache)
            st.session_state["edit_result_df"] = result_df
        except Exception as e:
            logger.error("Edit 탭 검색 중 오류 발생: %s", e)
            st.session_state["edit_result_df"] = None
            st.error(f"검색 중 오류가 발생했습니다: {e}")

def _merge_product_master(df: pd.DataFrame, use_cache: bool = True) -> pd.DataFrame:
    """기존 DESC 콜럼을 제거하고 PRODUCT_MASTER 데이터를 merge한다.

    Args:
        df (pd.DataFrame): SKU 콜럼을 포함한 원본 DataFrame.
        use_cache (bool): True이면 캐시된 PRODUCT_MASTER를 사용한다.

    Returns:
        pd.DataFrame: 품목명, 라인, 대분류, 중분류, 용량, 유통코드, 버전 콜럼이 추가된 DataFrame.
                      merge 실패 시 원본 df를 그대로 반환한다.
    """
    try:
        if "DESC" in df.columns:
            df = df.drop(columns=["DESC"])
        product_master = app_cache_load.load_product_master(use_cache=use_cache)
        product_master = product_master.rename(columns={
            "품목코드":        "SKU",
            "요청_품목명_국문": "품목명",
        })
        return df.merge(product_master, on="SKU", how="left")
    except Exception as e:
        logger.warning("PRODUCT_MASTER merge 실패, 원본 df 반환: %s", e)
        return df


def _result_df_edit(df: pd.DataFrame) -> pd.DataFrame:
    """SIGNOFF_DT 기준 최신 데이터만 남기고 SIGNOFF 우선 정책을 적용한다.

    KEY = FCST_MTH + DEPT + CHANNEL 단위로 중복 데이터를 정리한다.
    - 키별로 가장 최신 SIGNOFF_DT 행만 유지한다.
    - SIGNOFF 상태가 있는 키는 SIGNOFF 행만 남기고 나머지는 제거한다.

    Args:
        df (pd.DataFrame): MONTH_FORECAST_CONSOL 원본 DataFrame.

    Returns:
        pd.DataFrame: 중복 제거 및 SIGNOFF 정책 적용이 완료된 DataFrame.
    """
    # KEY = FCST_MTH + DEPT + CHANNEL (SIGNOFF_DT, REGISTANT 제외)
    df["KEY"] = df["FCST_MTH"].astype(str) + "_" + df["DEPT"].astype(str) + "_" + df["CHANNEL"].astype(str)

    # 1. 키별 SIGNOFF_DT 최신값만 남기기 (NaT인 행은 그대로 통과)
    df["SIGNOFF_DT"] = pd.to_datetime(df["SIGNOFF_DT"], errors="coerce", format="mixed")
    max_dt = df.groupby("KEY")["SIGNOFF_DT"].transform("max")
    df = df[df["SIGNOFF_DT"].isna() | (df["SIGNOFF_DT"] == max_dt)]

    # 2. SIGNOFF 상태가 있는 키 추출
    sign_off_keys = set(df[df["SIGN_STATUS"] == "SIGNOFF"]["KEY"].unique())

    # 3. SIGNOFF 있는 키 → SIGNOFF 행만, 없는 키 → 그대로
    if sign_off_keys:
        df = df[
            (df["KEY"].isin(sign_off_keys) & (df["SIGN_STATUS"] == "SIGNOFF")) |
            (~df["KEY"].isin(sign_off_keys))
        ]

    # 4. KEY 컬럼 삭제
    df = df.drop("KEY", axis=1).reset_index(drop=True)
    return df


def _build_pivot_df(df: pd.DataFrame, selected_levels: list) -> pd.DataFrame:
    """선택 계층과 MONTH 기준으로 FORECAST_QTY 피벗 테이블을 생성한다.

    합계 행, 평균 행, 평균 열, 합계 열을 포함하여 반환한다.

    Args:
        df (pd.DataFrame): FORECAST_QTY 컬럼을 포함한 검색 결과 DataFrame.
        selected_levels (list): 행 계층으로 사용할 컬럼명 리스트.

    Returns:
        pd.DataFrame: 계층·월 피벗 테이블 (합계/평균 행·열 포함).
    """
    pivot_df = (
        df.groupby(selected_levels + ["MONTH"])["FORECAST_QTY"]
        .sum()
        .reset_index()
        .pivot_table(
            index=selected_levels,
            columns="MONTH",
            values="FORECAST_QTY",
            aggfunc="sum",
            fill_value=0,
        )
    )
    # 월 컬럼 정렬 및 MultiIndex 단순화
    pivot_df = pivot_df.reindex(sorted(pivot_df.columns.tolist()), axis=1)
    pivot_df.columns.name = None

    # 평균 열 및 합계 열 추가
    pivot_df["평균"] = pivot_df.mean(axis=1).round(0)
    pivot_df["합계"] = pivot_df.drop(columns=["평균"]).sum(axis=1)

    # MultiIndex → 개별 컬럼으로 변환
    pivot_df = pivot_df.reset_index()

    # 평균 행 추가
    avg_row: dict = {col: pivot_df[col].mean() for col in pivot_df.columns if col not in selected_levels}
    for i, col in enumerate(selected_levels):
        avg_row[col] = "평균" if i == 0 else ""

    # 합계 행 추가
    total_row: dict = {col: pivot_df[col].sum() for col in pivot_df.columns if col not in selected_levels}
    for i, col in enumerate(selected_levels):
        total_row[col] = "합계" if i == 0 else ""

    pivot_df = pd.concat(
        [pivot_df, pd.DataFrame([total_row]), pd.DataFrame([avg_row])],
        ignore_index=True,
    )
    return pivot_df


def _calc_kpi_delta(df: pd.DataFrame, fcst_mth_list: list) -> tuple:
    """최신 등록 월과 직전 등록 월의 KPI delta 값을 계산한다.

    Args:
        df (pd.DataFrame): FORECAST_QTY, FCST_MTH 컬럼을 포함한 DataFrame.
        fcst_mth_list (list): 정렬된 등록 월 목록.

    Returns:
        tuple: (qty_delta: int | None, qty_delta_label: str | None,
                latest_mth: str | None, prev_mth: str | None)
    """
    if len(fcst_mth_list) < 2:
        return None, None, None, None

    latest_mth = fcst_mth_list[-1]
    prev_mth = fcst_mth_list[-2]
    latest_qty = int(df[df["FCST_MTH"] == latest_mth]["FORECAST_QTY"].sum())
    prev_qty = int(df[df["FCST_MTH"] == prev_mth]["FORECAST_QTY"].sum())
    qty_delta = latest_qty - prev_qty
    pct = f" ({qty_delta / prev_qty * 100:+.1f}%)" if prev_qty != 0 else ""
    qty_delta_label = f"{qty_delta:+,}{pct} (vs {prev_mth}→{latest_mth})"
    return qty_delta, qty_delta_label, latest_mth, prev_mth



def _render_sidebar() -> None:
    """Edit 탭 사이드바 필터 UI를 렌더링한다."""
    with st.sidebar:
        fcst_month_list = st.session_state.get("fcst_month_list", [])
        target_month_list = st.session_state.get("target_month_list", [])
        dept_list = st.session_state.get("dept_list", [])
        channel_list = st.session_state.get("channel_list", [])
        registant_list = st.session_state.get("registant_list", [])

        st.caption("MONTH_FORECAST_CONSOL 테이블 검색")

        if len(fcst_month_list) >= 2:
            st.select_slider(
                label="등록 월 - FCST_MTH",
                options=fcst_month_list,
                value=(fcst_month_list[-2], fcst_month_list[-1]),
                key="selectedfcst_month"
            )
        elif len(fcst_month_list) == 1:
            st.select_slider(
                label="등록 월 - FCST_MTH",
                options=fcst_month_list,
                value=(fcst_month_list[0], fcst_month_list[0]),
                key="selectedfcst_month"
            )
        else:
            st.session_state["selectedfcst_month"] = (None, None)
            st.info("등록 월 데이터 없음")

        if len(target_month_list) >= 2:
            st.select_slider(
                label="예측 월 - MONTH",
                options=target_month_list,
                value=(target_month_list[0], target_month_list[-1]),
                key="selected_target_month"
            )
        elif len(target_month_list) == 1:
            st.select_slider(
                label="예측 월 - MONTH",
                options=target_month_list,
                value=(target_month_list[0], target_month_list[0]),
                key="selected_target_month"
            )
        else:
            st.session_state["selected_target_month"] = (None, None)
            st.info("예측 월 데이터 없음")

        st.multiselect(label="사업부 - DEPT", options=dept_list, key="selected_dept")
        st.multiselect(label="채널 - CHANNEL", options=channel_list, key="selected_channel")
        st.multiselect(label="등록자 - REGISTANT", options=registant_list, key="selected_registant")

        st.write("")
        fcst_range = st.session_state.get("selectedfcst_month", (None, None))
        target_range = st.session_state.get("selected_target_month", (None, None))
        dept_str = ", ".join(st.session_state.get("selected_dept", []))
        channel_str = ", ".join(st.session_state.get("selected_channel", []))
        registant_str = ", ".join(st.session_state.get("selected_registant", []))

        with st.expander("검색 조건 확인", expanded=False):
            st.write(f"FCST_MTH : {fcst_range[0]} ~ {fcst_range[1]}")
            st.write(f"MONTH : {target_range[0]} ~ {target_range[1]}")
            st.write(f"DEPT : {dept_str}")
            st.write(f"CHANNEL : {channel_str}")
            st.write(f"REGISTANT : {registant_str}")

        st.write("")
        with st.expander("캐시 설정", expanded=False):
            st.toggle(
                label="필터 옵션 캐시 사용 (TTL 600s)",
                value=True,
                key="use_option_cache",
                help="비활성화 시 검색 시마다 Snowflake에서 직접 조회합니다.",
            )
            st.toggle(
                label="품목 마스터 캐시 사용 (TTL 3600s)",
                value=True,
                key="use_product_cache",
                help="비활성화 시 검색 시마다 PRODUCT_MASTER를 직접 조회합니다.",
            )

        st.write("")
        st.button(label="검색", type="primary", on_click=search_data, width="stretch")


def show_dashboard(df: pd.DataFrame) -> None:
    """검색 결과 DataFrame을 다중 선택 계층 기반 피벗 테이블로 표시한다.

    선택한 계층 컬럼 순서가 행 index가 되고, MONTH가 열이 되어
    FORECAST_QTY 합계를 피벗 테이블로 렌더링한다.

    Args:
        df (pd.DataFrame): search_data()로 조회된 결과 DataFrame.
    """
    df = df.copy()
    df["FORECAST_QTY"] = pd.to_numeric(df["FORECAST_QTY"], errors="coerce").fillna(0)
    df["MONTH"] = df["MONTH"].astype(str)
    df["FCST_MTH"] = df["FCST_MTH"].astype(str)

    # ── 계층 다중 선택 ────────────────────────────────────────────
    LEVEL_OPTIONS = [c for c in [
        "FCST_MTH", "DEPT", "CHANNEL", "SKU", "품목명",
        "라인", "대분류", "중분류", "용량", "유통코드", "버전",
    ] if c in df.columns]
    LEVEL_LABELS  = {
        "FCST_MTH": "등록 월 (FCST_MTH)",
        "DEPT":     "사업부 (DEPT)",
        "CHANNEL":  "채널 (CHANNEL)",
        "SKU":      "SKU",
        "품목명":    "품목명",
        "라인":      "라인",
        "대분류":    "대분류",
        "중분류":    "중분류",
        "용량":      "용량",
        "유통코드":  "유통코드",
        "버전":      "버전",
    }

    selected_levels: list = st.multiselect(
        "행 계층 선택 (순서대로 계층 구성, MONTH는 열로 고정)",
        options=LEVEL_OPTIONS,
        default=LEVEL_OPTIONS,
        format_func=lambda x: LEVEL_LABELS[x],
    )

    # df에 실제로 존재하는 컬럼만 유지 (PRODUCT_MASTER merge 실패 등으로 컬럼 부재 대비)
    selected_levels = [c for c in selected_levels if c in df.columns]

    if not selected_levels:
        st.info("행 계층을 1개 이상 선택해주세요.")
        return

    # ── KPI 카드 ──────────────────────────────────────────────────
    total_qty = int(df["FORECAST_QTY"].sum())
    fcst_mth_list = sorted(df["FCST_MTH"].unique().tolist())

    # 등록 월 2개 이상: 최신 월 vs 전월 대비 delta 계산
    qty_delta, qty_delta_label, _, _ = _calc_kpi_delta(df, fcst_mth_list)

    # ── 선택 계층별 동적 검색 필터 ────────────────────────────────
    with st.expander("상세 검색", expanded=True):
        filter_cols = st.columns(len(selected_levels))
        for i, level in enumerate(selected_levels):
            unique_vals = sorted(df[level].fillna("").astype(str).unique().tolist())
            selected_vals = filter_cols[i].multiselect(
                LEVEL_LABELS[level],
                options=unique_vals,
                default=[],
            )
            if selected_vals:
                df = df[df[level].astype(str).isin(selected_vals)]

    st.write("")
    st.subheader("대시보드")

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.metric("총 예측 수량", f"{total_qty:,}", delta=qty_delta_label)
    with kpi2:
        st.metric("SKU 수", f"{df['SKU'].nunique():,}")
    with kpi3:
        st.metric("채널 수", f"{df['CHANNEL'].nunique():,}")
    with kpi4:
        st.metric("예측 월 수", f"{df['MONTH'].nunique():,}")

    # ── 수량 변화 (Delta + Graph) ─────────────────────────────────
    if len(fcst_mth_list) >= 2:
        latest_mth = fcst_mth_list[-1]
        prev_mth   = fcst_mth_list[-2]
        with st.expander(f"수량 변화 `Delta` - `Graph`({prev_mth} → {latest_mth})", expanded=False):
            tab_delta, tab_graph = st.tabs(["Delta", "Graph"])

            with tab_delta:
                DELTA_LEVEL_OPTIONS = {
                    "등록 월 (FCST_MTH)":                    "FCST_MTH",
                    "등록 월 + 사업부 (DEPT)":               "DEPT",
                    "등록 월 + 사업부 + 채널 (DEPT+CHANNEL)": "CHANNEL",
                    "등록 월 + 사업부 + 채널 + SKU":          "SKU",
                }
                delta_level_label = st.radio(
                    "기준 계층 선택",
                    options=list(DELTA_LEVEL_OPTIONS.keys()),
                    index=0,
                    horizontal=True,
                    key="delta_level_radio",
                )
                delta_level = DELTA_LEVEL_OPTIONS[delta_level_label]
                level_vals = sorted(df[delta_level].astype(str).unique().tolist())
                cols = st.columns(min(len(level_vals), 6))
                for i, val in enumerate(level_vals):
                    # FCST_MTH 자체가 계층일 경우: val이 곧 등록월이므로
                    # val_df 필터와 FCST_MTH 비교가 중복되어 delta가 0이 되는 문제 방지
                    def _pct_str(diff: int, base: int) -> str:
                        if base == 0:
                            return ""
                        return f" ({diff / base * 100:+.1f}%)"

                    if delta_level == "FCST_MTH":
                        cur = int(df[df["FCST_MTH"] == latest_mth]["FORECAST_QTY"].sum()) if val == latest_mth else 0
                        prv = int(df[df["FCST_MTH"] == prev_mth]["FORECAST_QTY"].sum()) if val == prev_mth else 0
                        # 최신월 카드: value=최신월 수량, delta=최신-전월
                        # 전월 카드: value=전월 수량, delta=전월-최신월 (기준 대비 변화)
                        latest_total = int(df[df["FCST_MTH"] == latest_mth]["FORECAST_QTY"].sum())
                        prev_total = int(df[df["FCST_MTH"] == prev_mth]["FORECAST_QTY"].sum())
                        if val == latest_mth:
                            d = latest_total - prev_total
                            display_val = latest_total
                            display_delta = f"{d:+,}{_pct_str(d, prev_total)}"
                        elif val == prev_mth:
                            d = prev_total - latest_total
                            display_val = prev_total
                            display_delta = f"{d:+,}{_pct_str(d, latest_total)}"
                        else:
                            display_val = int(df[df["FCST_MTH"] == val]["FORECAST_QTY"].sum())
                            display_delta = None
                    else:
                        val_df = df[df[delta_level].astype(str) == val]
                        cur = int(val_df[val_df["FCST_MTH"] == latest_mth]["FORECAST_QTY"].sum())
                        prv = int(val_df[val_df["FCST_MTH"] == prev_mth]["FORECAST_QTY"].sum())
                        delta = cur - prv
                        display_val = cur
                        display_delta = f"{delta:+,}{_pct_str(delta, prv)}"
                    with cols[i % 6]:
                        with st.container(border=True):
                            st.metric(
                                label=val,
                                value=f"{display_val:,}",
                                delta=display_delta,
                            )

            with tab_graph:
                # 계층 선택
                CHART_LEVEL_OPTIONS = {
                    "사업부 (DEPT)":                ["DEPT"],
                    "사업부 + 채널 (DEPT+CHANNEL)": ["DEPT", "CHANNEL"],
                    "사업부 + 채널 + SKU":           ["DEPT", "CHANNEL", "SKU"],
                }
                chart_level = st.radio(
                    "계층 선택",
                    options=list(CHART_LEVEL_OPTIONS.keys()),
                    index=0,
                    horizontal=True,
                    key="chart_group_level",
                )
                group_cols = CHART_LEVEL_OPTIONS[chart_level]

                # 예측 월(MONTH) 필터
                month_list_all = sorted(df["MONTH"].astype(str).unique().tolist())
                selected_chart_months = st.multiselect(
                    "표시할 예측 월 선택 (비우면 전체)",
                    options=month_list_all,
                    default=[],
                    key="chart_month_filter",
                )
                chart_df = df.copy()
                if selected_chart_months:
                    chart_df = chart_df[chart_df["MONTH"].astype(str).isin(selected_chart_months)]

                # 계층별 집계 — x=MONTH, 선=계층+등록월 조합
                grp_keys = group_cols + ["MONTH"]
                agg_latest = (
                    chart_df[chart_df["FCST_MTH"].astype(str) == str(latest_mth)]
                    .groupby(grp_keys)["FORECAST_QTY"].sum().reset_index()
                )
                agg_prev = (
                    chart_df[chart_df["FCST_MTH"].astype(str) == str(prev_mth)]
                    .groupby(grp_keys)["FORECAST_QTY"].sum().reset_index()
                )

                all_months = sorted(
                    set(agg_latest["MONTH"].astype(str).tolist()) |
                    set(agg_prev["MONTH"].astype(str).tolist())
                )

                # 계층 고유값 (DEPT or DEPT+CHANNEL)
                def _grp_key(frame: pd.DataFrame) -> pd.Series:
                    return frame[group_cols].astype(str).apply("|".join, axis=1)

                all_groups = sorted(
                    set(list(_grp_key(agg_latest))) |
                    set(list(_grp_key(agg_prev)))
                )

                chart_tab1, chart_tab2 = st.tabs(["등록 월별 그래프", "변화량 (Delta Graph)"])

                # 색상 팔레트
                palette_prev   = ["#6c8ebf", "#82b366", "#9673a6", "#d6a520", "#ae4132", "#4d9696"]
                palette_latest = ["#d79b00", "#23445d", "#6a9153", "#5a3d6b", "#a0522d", "#1f6f6f"]

                with chart_tab1:
                    st.caption(f"""
💡 **사용법**
- 우측 범례에서 특정 사업부를 클릭하면 해당 선만 표기/미표기 변경 가능합니다.
- 예) *북미({prev_mth})* 와 *북미({latest_mth})* 만 선택하면 북미의 등록월별 수량 변화를 확인할 수 있습니다.
- 더블클릭 시 해당 선만 단독 표시됩니다.
""")
                    fig1 = go.Figure()
                    for gi, grp in enumerate(all_groups):
                        # 전월 선
                        sub_prev = agg_prev[
                            _grp_key(agg_prev) == grp
                        ].sort_values("MONTH")
                        fig1.add_trace(go.Scatter(
                            name=f"{grp} ({prev_mth})",
                            x=sub_prev["MONTH"].astype(str),
                            y=sub_prev["FORECAST_QTY"],
                            mode="lines+markers",
                            line=dict(color=palette_prev[gi % len(palette_prev)], dash="dot", width=2),
                            marker=dict(size=6),
                        ))
                        # 최신월 선
                        sub_latest = agg_latest[
                            _grp_key(agg_latest) == grp
                        ].sort_values("MONTH")
                        fig1.add_trace(go.Scatter(
                            name=f"{grp} ({latest_mth})",
                            x=sub_latest["MONTH"].astype(str),
                            y=sub_latest["FORECAST_QTY"],
                            mode="lines+markers",
                            line=dict(color=palette_latest[gi % len(palette_latest)], width=2),
                            marker=dict(size=6),
                        ))
                    fig1.update_layout(
                        xaxis_title="예측 월 (MONTH)",
                        xaxis=dict(type="category", categoryorder="category ascending"),
                        yaxis_title="FORECAST_QTY",
                        yaxis=dict(tickformat=",d"),
                        legend_title="계층 (등록월)",
                        height=450,
                        margin=dict(t=30, b=10),
                        hovermode="x unified",
                    )
                    st.plotly_chart(fig1, use_container_width=True)

                with chart_tab2:
                    st.caption(f"""
💡 **사용법**
- 우측 범례에서 사업부를 클릭하여 원하는 계층만 표시할 수 있습니다.
- 각 선은 *{latest_mth} 등록값 - {prev_mth} 등록값* 의 차이를 나타냅니다.
- 0선 위는 증가, 아래는 감소를 의미합니다.
""")
                    fig2 = go.Figure()
                    for gi, grp in enumerate(all_groups):
                        sub_prev = agg_prev[
                            _grp_key(agg_prev) == grp
                        ].sort_values("MONTH").set_index("MONTH")["FORECAST_QTY"]
                        sub_latest = agg_latest[
                            _grp_key(agg_latest) == grp
                        ].sort_values("MONTH").set_index("MONTH")["FORECAST_QTY"]
                        delta_s = (sub_latest.reindex(all_months, fill_value=0)
                                   - sub_prev.reindex(all_months, fill_value=0))
                        fig2.add_trace(go.Scatter(
                            name=grp,
                            x=delta_s.index.astype(str),
                            y=delta_s.values,
                            mode="lines+markers",
                            line=dict(color=palette_latest[gi % len(palette_latest)], width=2),
                            marker=dict(size=6),
                            fill="tozeroy",
                            fillcolor=f"rgba({int(palette_latest[gi % len(palette_latest)][1:3],16)},"
                                      f"{int(palette_latest[gi % len(palette_latest)][3:5],16)},"
                                      f"{int(palette_latest[gi % len(palette_latest)][5:7],16)},0.1)",
                        ))
                    fig2.add_hline(y=0, line_dash="dash", line_color="gray", line_width=1)
                    fig2.update_layout(
                        xaxis_title="예측 월 (MONTH)",
                        xaxis=dict(type="category", categoryorder="category ascending"),
                        yaxis_title=f"변화량 ({latest_mth} - {prev_mth})",
                        yaxis=dict(tickformat=",d"),
                        legend_title="계층",
                        height=450,
                        margin=dict(t=30, b=10),
                        hovermode="x unified",
                    )
                    st.plotly_chart(fig2, use_container_width=True)

    # ── 피벗 테이블 생성 ──────────────────────────────────────────
    with st.spinner("피벗 테이블 생성 중..."):
        pivot_df = _build_pivot_df(df, selected_levels)

    st.caption("피벗 데이터")

    # 월 컬럼 및 합계 컬럼만 숫자 포맷 적용 (계층 컬럼 제외)
    value_cols = [c for c in pivot_df.columns if c not in selected_levels]
    fmt = {col: "{:,.0f}" for col in value_cols}
    month_value_cols = [c for c in value_cols if c not in ("합계", "평균")]

    first_level_col = selected_levels[0]

    def _highlight_summary_rows(row: pd.Series) -> list:
        """합계·평균 행 전체에 배경색을 적용한다."""
        val = str(row[first_level_col])
        if val == "합계":
            return ["background-color: #cfe2ff"] * len(row)
        if val == "평균":
            return ["background-color: #fff3cd"] * len(row)
        return [""] * len(row)

    def _highlight_summary_cols(col: pd.Series) -> list:
        """합계·평균 열 전체에 배경색을 적용한다."""
        if col.name == "합계":
            return ["background-color: #cfe2ff"] * len(col)
        if col.name == "평균":
            return ["background-color: #fff3cd"] * len(col)
        return [""] * len(col)

    def _highlight_row_max(row: pd.Series) -> list:
        """데이터 행(합계·평균 행 제외)에서 MONTH 컬럼 최댓값 셀에 초록색 적용."""
        val = str(row[first_level_col])
        if val in ("합계", "평균"):
            return [""] * len(row)
        month_vals = row[month_value_cols]
        if month_vals.empty or month_vals.max() == 0:
            return [""] * len(row)
        styles = []
        for col in row.index:
            if col in month_value_cols and row[col] == month_vals.max():
                styles.append("background-color: #d4edda; font-weight: bold")
            else:
                styles.append("")
        return styles

    st.markdown(
        """
        <style>
        [data-testid="stDataFrame"] [class*="dvn-scroller"] [class*="gdg"] div[role="columnheader"] {
            font-weight: 700 !important;
            color: #000000 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.dataframe(
        pivot_df.style
        .format(fmt)
        .apply(_highlight_summary_rows, axis=1)
        .apply(_highlight_summary_cols, axis=0)
        .apply(_highlight_row_max, axis=1),
        width="stretch",
        height=min(60 + len(pivot_df) * 35, 600),
        hide_index=True,
    )
    st.caption(f"총 {len(df):,}건")

    display_cols = [c for c in [
        "FCST_MTH", "DEPT", "CHANNEL", "MONTH", "SKU", "DESC", "품목명",
        "라인", "대분류", "중분류", "용량", "유통코드", "버전",
        "FORECAST_QTY", "REGISTANT", "SIGN_STATUS", "SIGNOFF_DT",
    ] if c in df.columns]
    with st.expander("원본 데이터 보기"):
        raw_len = len(st.session_state.get("edit_result_df", df))
        st.caption(f"총 {raw_len:,}건")
        st.dataframe(df[display_cols].reset_index(drop=True), width="stretch")


def show_edit_page() -> None:
    """View 탭 페이지를 렌더링한다.

    사이드바 검색 필터와 검색 결과 대시보드로 구성된다.
    """
    st.caption(
        """등록된 예측 수량 데이터를 조회하고 계층별 피벗 테이블·KPI·추이 그래프로 시각화합니다.
        왼쪽 사이드바에서 등록 월·예측 월·사업부·채널·등록자 조건을 설정한 뒤 **검색** 버튼을 눌러주세요."""
    )

    if "option_df" not in st.session_state:
        init_data()

    _render_sidebar()

    result_df = st.session_state.get("edit_result_df")
    if result_df is None:
        st.info("사이드바에서 조건을 설정하고 검색 버튼을 눌러주세요.")
        return

    if result_df.empty:
        st.warning("조회된 데이터가 없습니다.")
        return

    st.caption(f"총 {len(result_df):,}건 조회됨")
    show_dashboard(result_df)