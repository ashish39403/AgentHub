import asyncio
import json
from dataclasses import dataclass
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.core.config import settings


@dataclass(frozen=True)
class ComposioConnectionRequest:
    provider: str
    configured: bool
    connect_url: str | None
    external_connection_id: str | None
    message: str
    raw_status: str | None = None


@dataclass(frozen=True)
class ComposioConnectedAccount:
    id: str
    provider: str
    status: str
    user_id: str | None
    account_email: str | None
    raw: dict


@dataclass(frozen=True)
class ComposioToolResult:
    successful: bool
    data: dict | list | str | None
    error: str | None
    raw: dict


class ComposioClient:
    def is_configured(self) -> bool:
        return bool(settings.composio_api_key)

    async def create_connection_request(
        self,
        *,
        user_id: str,
        provider: str,
        auth_config_id: str | None,
    ) -> ComposioConnectionRequest:
        if not self.is_configured():
            return ComposioConnectionRequest(
                provider=provider,
                configured=False,
                connect_url=None,
                external_connection_id=None,
                message="Set COMPOSIO_API_KEY to enable the Composio connection flow.",
            )
        if not auth_config_id:
            return ComposioConnectionRequest(
                provider=provider,
                configured=False,
                connect_url=None,
                external_connection_id=None,
                message=f"Set the Composio auth config id for {provider} before connecting this integration.",
            )

        body: dict = {
            "auth_config_id": auth_config_id,
            "user_id": user_id,
            "alias": f"agenthub-{provider}-{user_id}",
        }
        if settings.composio_callback_url:
            body["callback_url"] = settings.composio_callback_url

        response = await self.request_json("/connected_accounts/link", method="POST", body=body)
        connect_url = first_present(response, ["redirect_url", "redirectUrl", "url", "link", "auth_url"])
        connection_id = first_present(response, ["id", "connected_account_id", "connectedAccountId", "nanoid"])
        raw_status = first_present(response, ["status"])
        if not connect_url:
            connect_url = first_present(nested_dict(response, "connection_data", "val"), ["redirect_url", "redirectUrl"])
        if not connection_id:
            connection_id = first_present(nested_dict(response, "connection_data"), ["id", "connected_account_id"])

        return ComposioConnectionRequest(
            provider=provider,
            configured=True,
            connect_url=string_or_none(connect_url),
            external_connection_id=string_or_none(connection_id),
            raw_status=string_or_none(raw_status),
            message=(
                f"Open the Composio link to connect {provider}."
                if connect_url
                else f"Composio accepted the {provider} connection request, but did not return a link."
            ),
        )

    async def list_connected_accounts(
        self,
        *,
        user_id: str,
        provider: str,
        auth_config_id: str | None = None,
        connected_account_id: str | None = None,
    ) -> list[ComposioConnectedAccount]:
        if not self.is_configured():
            return []

        query: dict[str, list[str] | str | int] = {
            "toolkit_slugs": [provider],
            "user_ids": [user_id],
            "limit": 10,
        }
        if auth_config_id:
            query["auth_config_ids"] = [auth_config_id]
        if connected_account_id:
            query["connected_account_ids"] = [connected_account_id]

        response = await self.request_json("/connected_accounts", query=query)
        items = response.get("items") if isinstance(response, dict) else None
        if not isinstance(items, list):
            return []
        return [parse_connected_account(item, fallback_provider=provider) for item in items if isinstance(item, dict)]

    async def execute_tool(
        self,
        *,
        tool_slug: str,
        user_id: str,
        connected_account_id: str,
        arguments: dict | None = None,
        text: str | None = None,
    ) -> ComposioToolResult:
        body: dict = {
            "connected_account_id": connected_account_id,
            "user_id": user_id,
            "version": "latest",
        }
        if arguments is not None:
            body["arguments"] = arguments
        if text:
            body["text"] = text

        response = await self.request_json(f"/tools/execute/{tool_slug}", method="POST", body=body)
        successful = bool(response.get("successful", False)) if isinstance(response, dict) else False
        return ComposioToolResult(
            successful=successful,
            data=response.get("data") if isinstance(response, dict) else None,
            error=string_or_none(response.get("error")) if isinstance(response, dict) else "Invalid Composio response.",
            raw=response if isinstance(response, dict) else {},
        )

    async def delete_connected_account(self, connected_account_id: str) -> bool:
        if not self.is_configured() or not connected_account_id:
            return False
        response = await self.request_json(f"/connected_accounts/{connected_account_id}", method="DELETE")
        if not response:
            return True
        return bool(response.get("success", True)) if isinstance(response, dict) else True

    async def request_json(
        self,
        path: str,
        *,
        method: str = "GET",
        body: dict | None = None,
        query: dict[str, list[str] | str | int] | None = None,
    ) -> dict:
        if not settings.composio_api_key:
            return {}

        def request() -> dict:
            base_url = settings.composio_base_url.rstrip("/")
            url = f"{base_url}{path}"
            if query:
                url = f"{url}?{urlencode(query, doseq=True)}"
            request_body = json.dumps(body).encode("utf-8") if body is not None else None
            http_request = Request(
                url,
                data=request_body,
                method=method,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "x-api-key": settings.composio_api_key or "",
                },
            )
            with urlopen(http_request, timeout=20) as response:
                payload = response.read().decode("utf-8")
                return json.loads(payload) if payload else {}

        try:
            return await asyncio.to_thread(request)
        except Exception:
            return {}


def parse_connected_account(item: dict, *, fallback_provider: str) -> ComposioConnectedAccount:
    toolkit = item.get("toolkit") if isinstance(item.get("toolkit"), dict) else {}
    auth_config = item.get("auth_config") if isinstance(item.get("auth_config"), dict) else {}
    data = item.get("data") if isinstance(item.get("data"), dict) else {}
    state = item.get("state") if isinstance(item.get("state"), dict) else {}
    state_value = state.get("val") if isinstance(state.get("val"), dict) else {}

    return ComposioConnectedAccount(
        id=str(item.get("id") or item.get("nanoid") or ""),
        provider=str(toolkit.get("slug") or fallback_provider),
        status=str(item.get("status") or state_value.get("status") or "UNKNOWN"),
        user_id=string_or_none(item.get("user_id")),
        account_email=first_string(data, state_value, auth_config, keys=["email", "account_email", "login", "displayName"]),
        raw=item,
    )


def nested_dict(payload: dict, *keys: str) -> dict:
    current = payload
    for key in keys:
        value = current.get(key) if isinstance(current, dict) else None
        if not isinstance(value, dict):
            return {}
        current = value
    return current


def first_present(payload: dict, keys: list[str]) -> object | None:
    if not isinstance(payload, dict):
        return None
    for key in keys:
        value = payload.get(key)
        if value:
            return value
    return None


def first_string(*payloads: dict, keys: list[str]) -> str | None:
    for payload in payloads:
        value = first_present(payload, keys)
        if isinstance(value, str):
            return value
    return None


def string_or_none(value: object | None) -> str | None:
    return value if isinstance(value, str) and value.strip() else None


def get_composio_client() -> ComposioClient:
    return ComposioClient()
