"""Streamlit Cloud 배포 의존성 호환성 회귀 테스트."""

from pathlib import Path


REQUIREMENTS_PATH = Path(__file__).resolve().parents[1] / "requirements.txt"


def test_snowflake_security_versions_are_pinned() -> None:
    """Snowflake 보안 수정 버전과 SQLAlchemy 호환 핀이 고정됐는지 확인한다.

    Raises:
        AssertionError: requirements.txt에 보안 수정 버전 고정이 없을 때.
    """
    # 보안 수정이 포함된 Snowflake 릴리스와 호환 SQLAlchemy 버전을 고정한다.
    requirements = {
        line.strip().lower()
        for line in REQUIREMENTS_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }

    assert "sqlalchemy==2.0.54" in requirements
    assert "snowflake-sqlalchemy==1.11.0" in requirements
    assert "snowflake-connector-python==4.7.3" in requirements
    assert "pyarrow>=14.0.1,<24" in requirements
