"""Authenticated Unix domain socket IPC control server and client for CMP-02."""

from __future__ import annotations

import asyncio
import hmac
import json
import logging
import os
import socket
import stat
from collections.abc import Callable
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, SecretStr, ValidationError

from aira.ports.channel import (
    CancellationHandler,
    CancellationScope,
    CancellationSignal,
    CancelResult,
    ChannelType,
    SecurityAuditHandler,
    SecurityIngressEvent,
)

logger = logging.getLogger(__name__)


class IPCControlError(Exception):
    """Raised when local IPC server binding, auth, or transport fails."""


class IPCRequest(BaseModel):
    """Schema for authenticated newline-delimited JSON IPC control messages."""

    model_config = ConfigDict(frozen=True)

    action: Literal["cancel", "status"]
    auth_token: str
    requested_by: str = "local_cli"
    target_turn_id: str | None = None
    reason: str = "Local CLI IPC request"


class IPCResponse(BaseModel):
    """Schema for responses returned by the local IPC control server."""

    model_config = ConfigDict(frozen=True)

    ok: bool
    action: str
    cancel_result: CancelResult | None = None
    status: dict[str, Any] | None = None
    error: str | None = None


def _extract_secret(token: SecretStr | str | None) -> str:
    if token is None:
        return ""
    return (
        token.get_secret_value()
        if isinstance(token, SecretStr)
        else str(token)
    ).strip()


class LocalIPCServer:
    """Owner-only Unix domain socket server (0600) for cross-process cancel and status."""

    def __init__(
        self,
        *,
        socket_path: Path,
        auth_token: SecretStr | str,
        cancel_handler: CancellationHandler,
        status_provider: Callable[[], dict[str, Any]] | None = None,
        audit_handler: SecurityAuditHandler | None = None,
        max_payload_bytes: int = 16_384,
    ) -> None:
        token_value = _extract_secret(auth_token)
        if not token_value:
            raise IPCControlError("IPC_AUTH_TOKEN must be configured and non-empty.")

        self._socket_path = socket_path
        self._auth_token = token_value
        self._cancel_handler = cancel_handler
        self._status_provider = status_provider
        self._audit_handler = audit_handler
        self._max_payload_bytes = max_payload_bytes
        self._server: asyncio.AbstractServer | None = None

    @property
    def socket_path(self) -> Path:
        """Return configured Unix domain socket path."""
        return self._socket_path

    @property
    def is_running(self) -> bool:
        """Return True while the IPC server is actively bound."""
        return self._server is not None and self._server.is_serving()

    def _prepare_socket_path(self) -> None:
        self._socket_path.parent.mkdir(parents=True, exist_ok=True)
        if not self._socket_path.exists() and not self._socket_path.is_symlink():
            return

        st = self._socket_path.lstat()
        if not stat.S_ISSOCK(st.st_mode):
            raise IPCControlError(
                f"Refusing to overwrite non-socket path at {self._socket_path}."
            )

        # Verify whether a live listener still owns the socket before removing a stale file.
        probe = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        probe.settimeout(0.5)
        try:
            probe.connect(str(self._socket_path))
        except OSError:
            self._socket_path.unlink(missing_ok=True)
        else:
            raise IPCControlError(
                f"Another active process is already listening on {self._socket_path}."
            )
        finally:
            probe.close()

    async def start(self) -> None:
        """Bind Unix domain socket with strict 0600 permissions."""
        if self.is_running:
            return
        self._prepare_socket_path()
        try:
            self._server = await asyncio.start_unix_server(
                self._handle_client,
                path=str(self._socket_path),
                limit=self._max_payload_bytes,
            )
            os.chmod(self._socket_path, 0o600)
        except OSError as exc:
            self._server = None
            raise IPCControlError(f"Failed to start local IPC server: {exc}") from exc

    async def _handle_client(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        try:
            raw_line = await asyncio.wait_for(reader.readline(), timeout=5.0)
            if not raw_line:
                return
            try:
                req = IPCRequest.model_validate_json(raw_line.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError, ValidationError):
                await self._write_response(
                    writer,
                    IPCResponse(ok=False, action="unknown", error="Malformed IPC request."),
                )
                return

            if not hmac.compare_digest(
                req.auth_token.encode("utf-8"),
                self._auth_token.encode("utf-8"),
            ):
                if self._audit_handler is not None:
                    try:
                        await self._audit_handler.record_security_event(
                            SecurityIngressEvent(
                                event_type="SECURITY_INVALID_IPC_TOKEN",
                                channel=ChannelType.LOCAL_CLI,
                                sender_id=req.requested_by,
                                reason="Rejected local IPC control message with invalid token.",
                            )
                        )
                    except Exception as exc:  # noqa: BLE001
                        logger.warning("Failed to record IPC security audit event: %s", exc)
                await self._write_response(
                    writer,
                    IPCResponse(ok=False, action=req.action, error="Unauthorized IPC token."),
                )
                return

            if req.action == "status":
                status_data = (
                    self._status_provider()
                    if self._status_provider is not None
                    else {"status": "online"}
                )
                await self._write_response(
                    writer,
                    IPCResponse(ok=True, action="status", status=status_data),
                )
                return

            signal = CancellationSignal(
                source_channel=ChannelType.LOCAL_CLI,
                requested_by=req.requested_by,
                target_turn_id=req.target_turn_id,
                scope=(
                    CancellationScope.TURN
                    if req.target_turn_id
                    else CancellationScope.ALL_ACTIVE
                ),
                reason=req.reason,
            )
            cancel_res = await self._cancel_handler.handle_cancel(signal)
            await self._write_response(
                writer,
                IPCResponse(ok=True, action="cancel", cancel_result=cancel_res),
            )
        except asyncio.TimeoutError:
            await self._write_response(
                writer,
                IPCResponse(ok=False, action="unknown", error="IPC read timed out."),
            )
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except OSError:
                pass

    async def _write_response(self, writer: asyncio.StreamWriter, response: IPCResponse) -> None:
        payload = (response.model_dump_json() + "\n").encode("utf-8")
        writer.write(payload)
        await writer.drain()

    async def stop(self) -> None:
        """Close the IPC server and clean up the bound Unix socket cleanly."""
        if self._server is None:
            return
        self._server.close()
        await self._server.wait_closed()
        self._server = None
        try:
            if self._socket_path.exists() and stat.S_ISSOCK(self._socket_path.lstat().st_mode):
                self._socket_path.unlink(missing_ok=True)
        except OSError:
            pass


class LocalIPCClient:
    """Async Unix domain socket client used by the CLI for cross-process cancel/status."""

    def __init__(
        self,
        *,
        socket_path: Path,
        auth_token: SecretStr | str,
        timeout_seconds: float = 2.0,
    ) -> None:
        token_value = _extract_secret(auth_token)
        if not token_value:
            raise IPCControlError("IPC_AUTH_TOKEN must be configured to use IPC client.")
        self._socket_path = socket_path
        self._auth_token = token_value
        self._timeout_seconds = timeout_seconds

    async def send_cancel(
        self,
        *,
        target_turn_id: str | None = None,
        requested_by: str = "local_cli",
        reason: str = "Local CLI cancel command",
    ) -> CancelResult:
        """Send an authenticated cancellation request to a running AIRA daemon."""
        req = IPCRequest(
            action="cancel",
            auth_token=self._auth_token,
            requested_by=requested_by,
            target_turn_id=target_turn_id,
            reason=reason,
        )
        resp = await self._send_request(req)
        if not resp.ok or resp.cancel_result is None:
            raise IPCControlError(resp.error or "IPC cancel failed.")
        return resp.cancel_result

    async def fetch_status(self, *, requested_by: str = "local_cli") -> dict[str, Any]:
        """Request live runtime status over the authenticated IPC socket."""
        req = IPCRequest(
            action="status",
            auth_token=self._auth_token,
            requested_by=requested_by,
        )
        resp = await self._send_request(req)
        if not resp.ok or resp.status is None:
            raise IPCControlError(resp.error or "IPC status failed.")
        return resp.status

    async def _send_request(self, request: IPCRequest) -> IPCResponse:
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_unix_connection(str(self._socket_path)),
                timeout=self._timeout_seconds,
            )
        except (OSError, asyncio.TimeoutError) as exc:
            raise IPCControlError(
                f"Unable to connect to local IPC socket {self._socket_path}: {exc}"
            ) from exc

        try:
            writer.write((request.model_dump_json() + "\n").encode("utf-8"))
            await writer.drain()
            raw_reply = await asyncio.wait_for(reader.readline(), timeout=self._timeout_seconds)
            if not raw_reply:
                raise IPCControlError("Empty response from local IPC server.")
            return IPCResponse.model_validate_json(raw_reply.decode("utf-8"))
        except (OSError, asyncio.TimeoutError, UnicodeDecodeError, ValidationError) as exc:
            raise IPCControlError(f"IPC protocol failure: {exc}") from exc
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except OSError:
                pass
