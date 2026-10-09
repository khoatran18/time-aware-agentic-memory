import pytest
from langchain_core.language_models.fake_chat_models import FakeListChatModel

from tam.config.loader import Config, load_config
from tam.llm import registry
from tam.llm.factory import get_llm, get_llm_for_role


def cfg(**profiles):
    return Config({"llm": {"profiles": profiles, "roles": {"generation": "p"}}})


@pytest.fixture
def stub(monkeypatch):
    monkeypatch.setitem(registry.LLM_PROVIDERS, "stub", lambda profile: FakeListChatModel(responses=[profile["model_id"]]))


def test_get_llm_by_profile_name(stub):
    llm = get_llm(cfg(p={"provider": "stub", "model_id": "m1"}), "p")
    assert llm.invoke("hi").content == "m1"


def test_get_llm_for_role_follows_roles_to_profile(stub):
    assert get_llm_for_role(cfg(p={"provider": "stub", "model_id": "m2"}), "generation").invoke("x").content == "m2"


def test_unknown_profile_and_role_list_available(stub):
    c = cfg(p={"provider": "stub", "model_id": "m"})
    with pytest.raises(ValueError, match="llm.profiles.nope.*\\['p'\\]"):
        get_llm(c, "nope")
    with pytest.raises(ValueError, match="llm.roles.nope.*\\['generation'\\]"):
        get_llm_for_role(c, "nope")


def test_unknown_provider_lists_available():
    with pytest.raises(ValueError, match="'gemini'.*anthropic"):
        get_llm(cfg(p={"provider": "gemini", "model_id": "m"}), "p")


def test_duplicate_registration_rejected(stub):
    with pytest.raises(ValueError, match="đã được đăng ký"):
        registry.register_llm("stub")(lambda p: None)


def test_missing_api_key_names_profile():
    with pytest.raises(ValueError, match="llm.profiles.p.*api_key.*ANTHROPIC_API_KEY"):
        get_llm(cfg(p={"provider": "anthropic", "model_id": "claude-x", "api_key": None}), "p")


def test_placeholder_model_id_rejected():
    with pytest.raises(ValueError, match="llm.profiles.p.*model_id chưa điền"):
        get_llm(cfg(p={"provider": "openai", "model_id": "<điền model id>", "api_key": "sk-x"}), "p")


@pytest.mark.parametrize(
    "profile, cls_name",
    [
        ({"provider": "anthropic", "model_id": "claude-haiku-5-5", "api_key": "sk-x"}, "ChatAnthropic"),
        ({"provider": "openai", "model_id": "gpt-x", "api_key": "sk-x"}, "ChatOpenAI"),
        ({"provider": "ollama", "model_id": "llama-x"}, "ChatOllama"),  # không cần api_key
    ],
)
def test_real_providers_build_without_network(profile, cls_name):
    assert type(get_llm(cfg(p=profile), "p")).__name__ == cls_name


def test_real_configs_are_consistent():
    """Mọi role trỏ tới profile có thật; mọi profile dùng provider đã đăng ký."""
    for env in ("dev", "prod"):
        c = load_config(env)
        for role, profile in c.llm.roles.items():
            assert profile in c.llm.profiles, f"{env}: role {role} -> {profile}"
        for name, p in c.llm.profiles.items():
            assert p.provider in registry.LLM_PROVIDERS, f"{env}: profile {name}"
