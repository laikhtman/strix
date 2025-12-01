from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from strix.prompts import get_all_module_names, load_prompt_modules


def _jinja_env() -> Environment:
    prompts_dir = Path(__file__).parents[2] / "strix" / "prompts"
    return Environment(
        loader=FileSystemLoader(prompts_dir),
        autoescape=select_autoescape(enabled_extensions=(), default_for_string=False),
    )


def test_auth_playbook_module_available() -> None:
    modules = get_all_module_names()
    assert "oidc_saml_sso" in modules


def test_auth_playbook_renders() -> None:
    env = _jinja_env()
    content = load_prompt_modules(["oidc_saml_sso"], env)
    assert "oidc_saml_sso" in content
    assert "OIDC" in content["oidc_saml_sso"]
