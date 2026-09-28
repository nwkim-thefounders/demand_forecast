"""SIGNOFF_DT 생성 형식 회귀 테스트."""

import datetime

from app_03_DF_upload import _format_signoff_timestamp


def test_format_signoff_timestamp_includes_seconds() -> None:
    """SIGNOFF_DT가 초를 포함한 고정 길이 문자열인지 확인한다."""
    uploaded_at = datetime.datetime(2026, 9, 22, 2, 57, 0)

    assert _format_signoff_timestamp(uploaded_at) == "2026-09-22 02:57:00"
