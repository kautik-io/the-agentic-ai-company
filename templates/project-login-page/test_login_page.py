"""Smoke tests for project login page (page 1)."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOGIN = ROOT / "src" / "login"


def test_login_files_exist():
    assert (LOGIN / "index.html").is_file()
    assert (LOGIN / "login.css").is_file()
    assert (LOGIN / "login.js").is_file()


def test_login_html_has_form_fields():
    html = (LOGIN / "index.html").read_text(encoding="utf-8")
    assert 'id="email"' in html
    assert 'id="password"' in html
    assert 'id="role"' in html
    assert "Support Portal" in html


def test_login_js_has_demo_credentials():
    js = (LOGIN / "login.js").read_text(encoding="utf-8")
    assert "demo@support.com" in js
    assert "demo1234" in js


if __name__ == "__main__":
    test_login_files_exist()
    test_login_html_has_form_fields()
    test_login_js_has_demo_credentials()
    print("All login page tests passed")
