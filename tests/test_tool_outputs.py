import asyncio

from app.tools.internal_tools import draft_message
from app.tools.search_tool import web_search


def test_draft_message_creates_real_draft_not_instruction_echo() -> None:
    result = draft_message(
        {
            "recipient": "there",
            "purpose": "Use draft_message tool to draft a professional LinkedIn message asking a recruiter about software engineering internships.",
            "tone": "professional",
        }
    )

    assert result["send_status"] == "draft_only"
    assert result["recipient"] == "Recruiter"
    assert "software engineering internship" in result["draft"].lower()
    assert "Use draft_message tool" not in result["draft"]
    assert result["safety"] == "This is only a draft. No message was sent."


def test_web_search_returns_configuration_notice_when_keys_missing(monkeypatch) -> None:
    monkeypatch.setattr("app.tools.search_tool.settings.serper_api_key", None)
    monkeypatch.setattr("app.tools.search_tool.settings.serpapi_api_key", None)
    monkeypatch.setattr("app.tools.search_tool.settings.tavily_api_key", None)
    monkeypatch.setattr("app.tools.search_tool.settings.enable_tavily_fallback", False)

    result = asyncio.run(web_search({"query": "software engineering internships", "limit": 3}))

    assert result["status"] == "not_configured"
    assert result["live_search_used"] is False
    assert result["results"][0]["source"] == "local_configuration_notice"
    assert "SERPER_API_KEY" in result["next_step"]


def test_web_search_does_not_call_tavily_when_primary_search_is_missing(monkeypatch) -> None:
    monkeypatch.setattr("app.tools.search_tool.settings.serper_api_key", None)
    monkeypatch.setattr("app.tools.search_tool.settings.serpapi_api_key", None)
    monkeypatch.setattr("app.tools.search_tool.settings.tavily_api_key", "tavily-key")
    monkeypatch.setattr("app.tools.search_tool.settings.enable_tavily_fallback", True)

    async def fail_if_called(*args, **kwargs) -> dict:
        raise AssertionError("Tavily should not be called without primary search configured first.")

    monkeypatch.setattr("app.tools.search_tool.fetch_json", fail_if_called)

    result = asyncio.run(web_search({"query": "today latest general news", "limit": 3}))

    assert result["status"] == "not_configured"
    assert result["primary_provider"] == "not_configured"
    assert result["tavily_used"] is False
    assert result["fallback_used"] is False
    assert result["fallback_enabled"] is True
    assert result["live_search_used"] is False
    assert result["results"][0]["source"] == "local_configuration_notice"


def test_web_search_uses_serper_without_tavily_when_results_are_enough(monkeypatch) -> None:
    monkeypatch.setattr("app.tools.search_tool.settings.serper_api_key", "serper-key")
    monkeypatch.setattr("app.tools.search_tool.settings.serpapi_api_key", None)
    monkeypatch.setattr("app.tools.search_tool.settings.tavily_api_key", "tavily-key")
    monkeypatch.setattr("app.tools.search_tool.settings.enable_tavily_fallback", True)

    calls: list[str] = []

    async def fake_fetch_json(url: str, **kwargs) -> dict:
        calls.append(url)
        return {
            "organic": [
                {
                    "title": f"News result {index}",
                    "link": f"https://example.com/news-{index}",
                    "snippet": "This is a strong enough search snippet with enough useful detail for ranking.",
                }
                for index in range(1, 4)
            ]
        }

    monkeypatch.setattr("app.tools.search_tool.fetch_json", fake_fetch_json)

    result = asyncio.run(web_search({"query": "today latest general news", "limit": 3}))

    assert result["primary_provider"] == "serper"
    assert result["primary_results_enough"] is True
    assert result["tavily_used"] is False
    assert result["live_search_used"] is True
    assert {item["source"] for item in result["results"]} == {"serper"}
    assert calls == ["https://google.serper.dev/search"]


def test_web_search_uses_serpapi_when_serper_is_missing(monkeypatch) -> None:
    monkeypatch.setattr("app.tools.search_tool.settings.serper_api_key", None)
    monkeypatch.setattr("app.tools.search_tool.settings.serpapi_api_key", "serpapi-key")
    monkeypatch.setattr("app.tools.search_tool.settings.tavily_api_key", "tavily-key")
    monkeypatch.setattr("app.tools.search_tool.settings.enable_tavily_fallback", True)

    calls: list[str] = []

    async def fake_fetch_json(url: str, **kwargs) -> dict:
        calls.append(url)
        return {
            "organic_results": [
                {
                    "title": f"SerpAPI result {index}",
                    "link": f"https://example.com/serpapi-{index}",
                    "snippet": "This SerpAPI snippet has enough useful detail for the search result quality check.",
                }
                for index in range(1, 4)
            ]
        }

    monkeypatch.setattr("app.tools.search_tool.fetch_json", fake_fetch_json)

    result = asyncio.run(web_search({"query": "today latest general news", "limit": 3}))

    assert result["primary_provider"] == "serpapi"
    assert result["primary_results_enough"] is True
    assert result["tavily_used"] is False
    assert result["live_search_used"] is True
    assert {item["source"] for item in result["results"]} == {"serpapi"}
    assert calls[0].startswith("https://serpapi.com/search.json?")


def test_web_search_skips_tavily_by_default_when_serper_is_weak(monkeypatch) -> None:
    monkeypatch.setattr("app.tools.search_tool.settings.serper_api_key", "serper-key")
    monkeypatch.setattr("app.tools.search_tool.settings.serpapi_api_key", None)
    monkeypatch.setattr("app.tools.search_tool.settings.tavily_api_key", "tavily-key")
    monkeypatch.setattr("app.tools.search_tool.settings.enable_tavily_fallback", False)

    calls: list[str] = []

    async def fake_fetch_json(url: str, **kwargs) -> dict:
        calls.append(url)
        return {
            "organic": [
                {
                    "title": "Thin result",
                    "link": "https://example.com/thin",
                    "snippet": "Too short",
                }
            ]
        }

    monkeypatch.setattr("app.tools.search_tool.fetch_json", fake_fetch_json)

    result = asyncio.run(web_search({"query": "today latest general news", "limit": 3}))

    assert result["primary_provider"] == "serper"
    assert result["primary_results_enough"] is False
    assert result["tavily_used"] is False
    assert result["fallback_used"] is False
    assert result["fallback_enabled"] is False
    assert {item["source"] for item in result["results"]} == {"serper"}
    assert calls == ["https://google.serper.dev/search"]


def test_web_search_combines_serper_and_tavily_when_fallback_is_enabled(monkeypatch) -> None:
    monkeypatch.setattr("app.tools.search_tool.settings.serper_api_key", "serper-key")
    monkeypatch.setattr("app.tools.search_tool.settings.serpapi_api_key", None)
    monkeypatch.setattr("app.tools.search_tool.settings.tavily_api_key", "tavily-key")
    monkeypatch.setattr("app.tools.search_tool.settings.enable_tavily_fallback", True)

    async def fake_fetch_json(url: str, **kwargs) -> dict:
        if "google.serper.dev" in url:
            return {
                "organic": [
                    {
                        "title": "Thin result",
                        "link": "https://example.com/thin",
                        "snippet": "Too short",
                    }
                ]
            }
        return {
            "results": [
                {
                    "title": "Tavily fuller result",
                    "url": "https://example.com/tavily",
                    "content": "Tavily returned a richer result with enough context for the LLM to compare.",
                    "score": 0.91,
                }
            ]
        }

    monkeypatch.setattr("app.tools.search_tool.fetch_json", fake_fetch_json)

    result = asyncio.run(web_search({"query": "today latest general news", "limit": 3}))

    assert result["primary_provider"] == "serper"
    assert result["primary_results_enough"] is False
    assert result["tavily_used"] is True
    assert result["fallback_used"] is True
    assert {item["source"] for item in result["results"]} == {"serper", "tavily"}
    assert result["rewritten_query"] == "today latest general news latest practical sources"
