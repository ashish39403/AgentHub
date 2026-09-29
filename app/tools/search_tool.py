from app.core.config import settings


async def web_search(arguments: dict) -> dict:
    query = str(arguments.get("query", "")).strip()
    limit = int(arguments.get("limit", 5))
    if not query:
        raise ValueError("query is required")

    serp_results = await search_serpapi(query=query, limit=limit)
    if serp_results:
        results = serp_results
        fallback_used = False
        rewritten_query = None
    else:
        rewritten_query = rewrite_query(query)
        tavily_results = await search_tavily(query=rewritten_query, limit=limit)
        results = tavily_results
        fallback_used = True

    ranked_results = rank_results(results)[:limit]
    return {
        "query": query,
        "rewritten_query": rewritten_query,
        "fallback_used": fallback_used,
        "headline": build_headline(ranked_results, query),
        "results": ranked_results,
    }


async def search_serpapi(*, query: str, limit: int) -> list[dict]:
    if not settings.serpapi_api_key:
        return []
    return [
        {
            "title": f"SerpAPI result for {query}",
            "url": "https://example.com/serpapi-result",
            "snippet": "Live SerpAPI integration will be wired after credentials are configured.",
            "source": "serpapi",
            "score": 80,
        }
    ][:limit]


async def search_tavily(*, query: str, limit: int) -> list[dict]:
    if not settings.tavily_api_key:
        return [
            {
                "title": f"Research seed for {query}",
                "url": "https://example.com/research-seed",
                "snippet": "Set TAVILY_API_KEY for live fallback search. This deterministic result keeps local development testable.",
                "source": "local_fallback",
                "score": 50,
            }
        ][:limit]
    return [
        {
            "title": f"Tavily result for {query}",
            "url": "https://example.com/tavily-result",
            "snippet": "Live Tavily integration will be wired after credentials are configured.",
            "source": "tavily",
            "score": 75,
        }
    ][:limit]


def rewrite_query(query: str) -> str:
    return f"{query} latest practical sources"


def rank_results(results: list[dict]) -> list[dict]:
    deduped: dict[str, dict] = {}
    for result in results:
        deduped[result["url"]] = result
    return sorted(deduped.values(), key=lambda result: result.get("score", 0), reverse=True)


def build_headline(results: list[dict], query: str) -> str:
    if not results:
        return f"No strong results found for {query}."
    return f"Top research result for {query}: {results[0]['title']}"
