"""app_99_regist_edit.py 비즈니스 로직 단위 테스트.

테스트 대상:
- _result_df_edit: SIGNOFF 우선 정책, 최신 SIGNOFF_DT 필터
- _build_pivot_df: 피벗 생성, 합계/평균 행·열 포함 여부
- _calc_kpi_delta: delta 계산, 퍼센트, None 반환 케이스
"""

import sys
import os
import pytest
import pandas as pd
from datetime import datetime

# 프로젝트 루트를 sys.path에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Streamlit 및 plotly 의존성을 mock으로 대체 (UI 없이 로직만 테스트)
import unittest.mock as mock
sys.modules.setdefault("streamlit", mock.MagicMock())
sys.modules.setdefault("plotly", mock.MagicMock())
sys.modules.setdefault("plotly.graph_objects", mock.MagicMock())
sys.modules.setdefault("snowflake_SQL", mock.MagicMock())
sys.modules.setdefault("app_cache_load", mock.MagicMock())

from app_99_regist_edit import _result_df_edit, _build_pivot_df, _calc_kpi_delta


# ── 테스트용 픽스처 ────────────────────────────────────────────────────────────

def _make_forecast_df() -> pd.DataFrame:
    """기본 테스트용 MONTH_FORECAST_CONSOL 형태 DataFrame."""
    return pd.DataFrame({
        "FCST_MTH":    ["202505", "202505", "202506", "202506"],
        "DEPT":        ["A", "A", "A", "A"],
        "CHANNEL":     ["CH1", "CH1", "CH1", "CH1"],
        "MONTH":       ["202507", "202507", "202507", "202507"],
        "SKU":         ["S001", "S001", "S001", "S001"],
        "FORECAST_QTY": [100, 200, 300, 400],
        "REGISTANT":   ["user1", "user1", "user1", "user1"],
        "SIGN_STATUS": ["REGIST", "REGIST", "REGIST", "REGIST"],
        "SIGNOFF_DT":  [
            "2025-05-01 10:00:00",
            "2025-05-02 10:00:00",
            "2025-06-01 10:00:00",
            "2025-06-02 10:00:00",
        ],
    })


# ── _result_df_edit 테스트 ─────────────────────────────────────────────────────

class TestResultDfEdit:
    def test_keeps_latest_signoff_dt(self):
        """같은 KEY 내에서 SIGNOFF_DT 최신 행만 유지해야 한다."""
        df = _make_forecast_df().iloc[:2].copy()  # 같은 KEY, 두 행
        result = _result_df_edit(df)
        # 2025-05-02가 더 최신 → 200만 남아야 함
        assert len(result) == 1
        assert int(result["FORECAST_QTY"].iloc[0]) == 200

    def test_signoff_wins_over_regist(self):
        """같은 KEY에 SIGNOFF와 REGIST가 공존하면 SIGNOFF 행만 남아야 한다."""
        df = pd.DataFrame({
            "FCST_MTH":    ["202505", "202505"],
            "DEPT":        ["A", "A"],
            "CHANNEL":     ["CH1", "CH1"],
            "MONTH":       ["202507", "202507"],
            "SKU":         ["S001", "S001"],
            "FORECAST_QTY": [100, 999],
            "REGISTANT":   ["user1", "user1"],
            "SIGN_STATUS": ["REGIST", "SIGNOFF"],
            "SIGNOFF_DT":  ["2025-05-01 10:00", "2025-05-01 10:00"],
        })
        result = _result_df_edit(df)
        assert len(result) == 1
        assert result["SIGN_STATUS"].iloc[0] == "SIGNOFF"
        assert int(result["FORECAST_QTY"].iloc[0]) == 999

    def test_different_keys_both_kept(self):
        """KEY가 다른 행은 각각 유지되어야 한다."""
        df = pd.DataFrame({
            "FCST_MTH":    ["202505", "202506"],
            "DEPT":        ["A", "B"],
            "CHANNEL":     ["CH1", "CH1"],
            "MONTH":       ["202507", "202507"],
            "SKU":         ["S001", "S001"],
            "FORECAST_QTY": [100, 200],
            "REGISTANT":   ["user1", "user1"],
            "SIGN_STATUS": ["REGIST", "REGIST"],
            "SIGNOFF_DT":  ["2025-05-01 10:00", "2025-06-01 10:00"],
        })
        result = _result_df_edit(df)
        assert len(result) == 2

    def test_key_column_removed(self):
        """결과에 'KEY' 컬럼이 없어야 한다."""
        df = _make_forecast_df().iloc[:1].copy()
        result = _result_df_edit(df)
        assert "KEY" not in result.columns


# ── _build_pivot_df 테스트 ────────────────────────────────────────────────────

class TestBuildPivotDf:
    def _sample_df(self) -> pd.DataFrame:
        return pd.DataFrame({
            "DEPT":         ["A", "A", "B", "B"],
            "MONTH":        ["202507", "202508", "202507", "202508"],
            "FORECAST_QTY": [100, 200, 300, 400],
        })

    def test_pivot_contains_month_columns(self):
        """MONTH 값이 피벗 컬럼으로 존재해야 한다."""
        df = self._sample_df()
        result = _build_pivot_df(df, ["DEPT"])
        assert "202507" in result.columns
        assert "202508" in result.columns

    def test_pivot_contains_sum_avg_columns(self):
        """합계, 평균 컬럼이 존재해야 한다."""
        df = self._sample_df()
        result = _build_pivot_df(df, ["DEPT"])
        assert "합계" in result.columns
        assert "평균" in result.columns

    def test_pivot_contains_total_avg_rows(self):
        """합계 행과 평균 행이 존재해야 한다."""
        df = self._sample_df()
        result = _build_pivot_df(df, ["DEPT"])
        first_col = "DEPT"
        labels = result[first_col].astype(str).tolist()
        assert "합계" in labels
        assert "평균" in labels

    def test_total_row_sum_correct(self):
        """합계 행의 202507 값은 A+B = 400이어야 한다."""
        df = self._sample_df()
        result = _build_pivot_df(df, ["DEPT"])
        total_row = result[result["DEPT"].astype(str) == "합계"]
        assert not total_row.empty
        assert int(total_row["202507"].iloc[0]) == 400

    def test_multi_level_pivot(self):
        """DEPT + CHANNEL 다중 계층도 정상 생성되어야 한다."""
        df = pd.DataFrame({
            "DEPT":         ["A", "A"],
            "CHANNEL":      ["CH1", "CH2"],
            "MONTH":        ["202507", "202507"],
            "FORECAST_QTY": [100, 200],
        })
        result = _build_pivot_df(df, ["DEPT", "CHANNEL"])
        assert "DEPT" in result.columns
        assert "CHANNEL" in result.columns


# ── _calc_kpi_delta 테스트 ────────────────────────────────────────────────────

class TestCalcKpiDelta:
    def _sample_df(self) -> pd.DataFrame:
        return pd.DataFrame({
            "FCST_MTH":    ["202505", "202505", "202506", "202506"],
            "FORECAST_QTY": [100, 100, 150, 150],
        })

    def test_returns_none_when_single_month(self):
        """등록 월이 1개이면 delta가 None이어야 한다."""
        df = pd.DataFrame({
            "FCST_MTH": ["202505"],
            "FORECAST_QTY": [100],
        })
        delta, label, latest, prev = _calc_kpi_delta(df, ["202505"])
        assert delta is None
        assert label is None
        assert latest is None
        assert prev is None

    def test_correct_delta_value(self):
        """202506(300) - 202505(200) = +100이어야 한다."""
        df = self._sample_df()
        delta, label, latest, prev = _calc_kpi_delta(df, ["202505", "202506"])
        assert delta == 100

    def test_delta_label_contains_percent(self):
        """label에 퍼센트 표기가 포함되어야 한다."""
        df = self._sample_df()
        _, label, _, _ = _calc_kpi_delta(df, ["202505", "202506"])
        assert "%" in label

    def test_latest_and_prev_month_correct(self):
        """latest_mth와 prev_mth가 올바르게 반환되어야 한다."""
        df = self._sample_df()
        _, _, latest, prev = _calc_kpi_delta(df, ["202505", "202506"])
        assert latest == "202506"
        assert prev == "202505"

    def test_zero_base_no_percent_error(self):
        """prev_qty가 0일 때 ZeroDivisionError 없이 처리되어야 한다."""
        df = pd.DataFrame({
            "FCST_MTH":    ["202505", "202506"],
            "FORECAST_QTY": [0, 100],
        })
        delta, label, _, _ = _calc_kpi_delta(df, ["202505", "202506"])
        assert delta == 100
        assert label is not None
