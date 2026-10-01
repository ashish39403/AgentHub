import asyncio
import json
from urllib.request import Request, urlopen

from app.core.config import settings


async def web_search(arguments: dict) -> dict:
    query = str(arguments.get("query", "")).strip()
    limit = int(arguments.get("limit", 5))
    if not query:
        raise ValueError("query is required")

    if not has_primary_search_key():
        ranked_results = [search_configuration_notice(query)]
        return {
            "status": "not_configured",
            "query": query,
            "rewritten_query": None,
            "primary_provider": "not_configured",
            "primary_result_count": 0,
            "primary_results_enough": False,
            "tavily_used": False,
            "fallback_used": False,
            "fallback_enabled": settings.enable_tavily_fallback,
            "live_search_used": False,
            "headline": build_headline(ranked_results, query),
            "results": ranked_results,
            "next_step": next_step_for_search(
                ranked_results,
                primary_results_enough=False,
                tavily_used=False,
            ),
        }

    primary_results = await search_primary_provider(query=query, limit=limit)
    primary_enough = has_enough_results(primary_results, limit=limit)
    tavily_results: list[dict] = []
    rewritten_query = None

    if not primary_enough and settings.enable_tavily_fallback and settings.tavily_api_key:
        rewritten_query = rewrite_query(query)
        tavily_results = await search_tavily(query=rewritten_query, limit=limit)

    results = [*primary_results, *tavily_results]
    ranked_results = rank_results(results)[:limit]
    return {
        "status": search_status(ranked_results),
        "query": query,
        "rewritten_query": rewritten_query,
        "primary_provider": primary_provider_name(),
        "primary_result_count": len(primary_results),
        "primary_results_enough": primary_enough,
        "tavily_used": bool(tavily_results),
        "fallback_used": bool(tavily_results),
        "fallback_enabled": settings.enable_tavily_fallback,
        "live_search_used": any(result.get("source") in {"serper", "tavily"} for result in ranked_results),
        "headline": build_headline(ranked_results, query),
        "results": ranked_results,
        "next_step": next_step_for_search(
            ranked_results,
            primary_results_enough=primary_enough,
            tavily_used=bool(tavily_results),
        ),
    }


def primary_provider_name() -> str:
    if settings.serper_api_key:
        return "serper"
    return "not_configured"


def has_primary_search_key() -> bool:
    return bool(settings.serper_api_key)


async def search_primary_provider(*, query: str, limit: int) -> list[dict]:
    return await search_serper(query=query, limit=limit)


async def search_serper(*, query: str, limit: int) -> list[dict]:
    if not settings.serper_api_key:
        return []

    payload = await fetch_json(
        "https://google.serper.dev/search",
        method="POST",
        body={"q": query, "num": limit},
        headers={"X-API-KEY": settings.serper_api_key},
    )
    organic_results = payload.get("organic") if isinstance(payload, dict) else None
    if not isinstance(organic_results, list):
        return []

    return [
        {
            "title": str(result.get("title") or "Untitled result"),
            "url": result.get("link"),
            "snippet": str(result.get("snippet") or ""),
            "source": "serper",
            "score": max(100 - index, 1),
        }
        for index, result in enumerate(organic_results[:limit])
        if isinstance(result, dict)
    ]


async def search_tavily(*, query: str, limit: int = 5) -> list[dict]:
    if not settings.tavily_api_key:
        return []
    request_body = {
        "api_key": settings.tavily_api_key,
        "query": query,
        "max_results": limit,
        "search_depth": "basic",
    }
    payload = await fetch_json("https://api.tavily.com/search", method="POST", body=request_body)
    results = payload.get("results") if isinstance(payload, dict) else None
    if not isinstance(results, list):
        return []
    return [
        {
            "title": str(result.get("title") or "Untitled result"),
            "url": result.get("url"),
            "snippet": str(result.get("content") or ""),
            "source": "tavily",
            "score": int(float(result.get("score", 0.5)) * 100) if result.get("score") is not None else max(75 - index, 1),
        }
        for index, result in enumerate(results[:limit])
        if isinstance(result, dict)
    ][:limit]


def rewrite_query(query: str) -> str:
    return f"{query} latest practical sources"


def has_enough_results(results: list[dict], *, limit: int) -> bool:
    if not results:
        return False

    minimum_results = min(3, limit)
    strong_results = [
        result
        for result in results
        if result.get("url") and result.get("title") and len(str(result.get("snippet") or "")) >= 40
    ]
    return len(strong_results) >= minimum_results


def rank_results(results: list[dict]) -> list[dict]:
    deduped: dict[str, dict] = {}
    for result in results:
        deduped[str(result.get("url") or result.get("title"))] = result
    return sorted(deduped.values(), key=lambda result: result.get("score", 0), reverse=True)


def build_headline(results: list[dict], query: str) -> str:
    if not results:
        return f"No strong results found for {query}."
    if results[0].get("source") == "local_configuration_notice":
        return f"Live search is not configured yet for {query}."
    return f"Top research result for {query}: {results[0]['title']}"


def next_step_for_search(results: list[dict], *, primary_results_enough: bool, tavily_used: bool) -> str:
    if results and results[0].get("source") == "local_configuration_notice":
        return "Add SERPER_API_KEY to .env, then restart the backend. Tavily fallback is disabled by default."
    if not primary_results_enough and not tavily_used:
        return "Primary search ran but results were weak. Tavily was not called because ENABLE_TAVILY_FALLBACK is false, missing, or TAVILY_API_KEY is not set."
    return "Review the ranked results and summarize the most relevant findings for the user."


def search_status(results: list[dict]) -> str:
    if not results:
        return "no_results"
    if results[0].get("source") == "local_configuration_notice":
        return "not_configured"
    return "succeeded"


def search_configuration_notice(query: str) -> dict:
    return {
        "title": f"Primary search is not configured for: {query}",
        "url": None,
        "snippet": "Set SERPER_API_KEY in .env to enable live web search. Tavily fallback is disabled by default, so it was not called.",
        "source": "local_configuration_notice",
        "score": 10,
    }


async def fetch_json(
    url: str,
    *,
    method: str = "GET",
    body: dict | None = None,
    headers: dict[str, str] | None = None,
) -> dict:
    def request_json() -> dict:
        encoded_body = json.dumps(body).encode("utf-8") if body is not None else None
        request = Request(
            url,
            data=encoded_body,
            method=method,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                **(headers or {}),
            },
        )
        with urlopen(request, timeout=12) as response:
            return json.loads(response.read().decode("utf-8"))

    try:
        return await asyncio.to_thread(request_json)
    except Exception:
        return {}
