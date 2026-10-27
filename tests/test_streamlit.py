from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_streamlit_smoke():
    app = Path(__file__).resolve().parents[1] / "app.py"
    test = AppTest.from_file(str(app), default_timeout=20).run()
    assert not test.exception
    assert any("光伏供应链研究终端" in title.value for title in test.title)
