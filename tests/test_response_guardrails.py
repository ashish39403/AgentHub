import json

from app.agents.guardrails import guardrail_assistant_response


def test_guardrail_extracts_user_facing_answer_from_json() -> None:
    content = json.dumps({"status": "succeeded", "answer": "Here is the clean final answer."})

    assert guardrail_assistant_response(content) == "Here is the clean final answer."


def test_guardrail_formats_search_like_json_without_internal_status() -> None:
    content = json.dumps(
        {
            "status": "succeeded",
            "query": "latest internships",
            "results": [
                {
                    "title": "Backend Internship",
                    "url": "https://example.com/job",
                    "snippet": "Remote backend internship for students.",
                }
            ],
            "raw_result": {"debug": True},
        }
    )

    guarded = guardrail_assistant_response(content)

    assert "Backend Internship" in guarded
    assert "https://example.com/job" in guarded
    assert "raw_result" not in guarded
    assert "status" not in guarded.lower()


def test_guardrail_unwraps_fenced_json() -> None:
    content = """```json
{"message": "This is a clean message."}
```"""

    assert guardrail_assistant_response(content) == "This is a clean message."


def test_guardrail_keeps_normal_markdown_response() -> None:
    content = "**Summary**\n- Your agent is working well."

    assert guardrail_assistant_response(content) == content
