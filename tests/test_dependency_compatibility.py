"""Streamlit Cloud 배포 의존성 호환성 회귀 테스트."""

from pathlib import Path


REQUIREMENTS_PATH = Path(__file__).resolve().parents[1] / "requirements.txt"


def test_sqlalchemy_version_is_pinned_to_verified_release() -> None:
    """Snowflake dialect와 검증된 SQLAlchemy 버전이 고정됐는지 확인한다.

    Raises:
        AssertionError: requirements.txt에 검증된 버전 고정이 없을 때.
    """
    # Cloud가 호환되지 않는 SQLAlchemy 2.1 계열을 자동 설치하지 못하게 한다.
    requirements = {
        line.strip().lower()
        for line in REQUIREMENTS_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }

    assert "sqlalchemy==2.0.54" in requirements
