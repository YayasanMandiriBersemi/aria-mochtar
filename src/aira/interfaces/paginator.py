"""Outbound message pagination with fenced Markdown code block preservation."""

from __future__ import annotations

TELEGRAM_MAX_MESSAGE_LENGTH = 4096


class MessagePaginator:
    """Splits oversized text into bounded chunks while keeping Markdown fences valid."""

    def __init__(self, max_length: int = TELEGRAM_MAX_MESSAGE_LENGTH) -> None:
        if max_length < 64:
            raise ValueError("max_length must be at least 64 characters.")
        self._max_length = max_length

    @property
    def max_length(self) -> int:
        """Return maximum characters allowed per delivered message chunk."""
        return self._max_length

    def paginate(self, text: str) -> list[str]:
        """Split text into chunks strictly <= max_length, preserving code fences."""
        if len(text) <= self._max_length:
            return [text]

        # Start with a header budget covering up to "[999/999]\n" (10 chars).
        header_budget = 10
        bodies = self._split_bodies(text, header_budget=header_budget)
        total = len(bodies)
        actual_header_len = len(f"[{total}/{total}]\n")

        if actual_header_len > header_budget:
            bodies = self._split_bodies(text, header_budget=actual_header_len + 2)
            total = len(bodies)

        if total == 1 and len(bodies[0]) <= self._max_length:
            return bodies

        return [f"[{idx}/{total}]\n{body}" for idx, body in enumerate(bodies, start=1)]

    def _split_bodies(self, text: str, *, header_budget: int) -> list[str]:
        """Partition text into raw chunk bodies leaving room for [k/N] prefixes."""
        chunks: list[str] = []
        current_parts: list[str] = []
        current_len = 0
        open_fence: str | None = None

        def close_cost(fence: str | None, buf_parts: list[str]) -> int:
            if fence is None:
                return 0
            ends_with_nl = bool(buf_parts and buf_parts[-1].endswith("\n"))
            return 3 if ends_with_nl else 4  # "```" or "\n```"

        def flush_current(reopen_fence: str | None) -> None:
            nonlocal current_parts, current_len
            if not current_parts:
                return
            body = "".join(current_parts)
            if open_fence is not None:
                body = body + ("```" if body.endswith("\n") else "\n```")
            chunks.append(body)
            current_parts = []
            current_len = 0
            if reopen_fence is not None:
                opener = f"{reopen_fence}\n"
                current_parts.append(opener)
                current_len = len(opener)

        def remaining_body_capacity(fence_after_add: str | None) -> int:
            return self._max_length - header_budget - close_cost(fence_after_add, current_parts)

        lines = text.splitlines(keepends=True)
        for line in lines:
            stripped = line.strip()
            is_fence_toggle = stripped.startswith("```") and len(stripped) <= 32
            next_fence = open_fence

            if is_fence_toggle:
                if open_fence is None:
                    next_fence = stripped
                elif stripped == "```":
                    next_fence = None

            # Check if appending this full line fits cleanly.
            projected_len = current_len + len(line)
            max_allowed = self._max_length - header_budget - close_cost(next_fence, [line])
            if projected_len <= max_allowed:
                current_parts.append(line)
                current_len = projected_len
                open_fence = next_fence
                continue

            # If we have accumulated content, flush it before handling this line.
            if current_parts and not (
                len(current_parts) == 1
                and open_fence is not None
                and current_parts[0] == f"{open_fence}\n"
            ):
                flush_current(reopen_fence=open_fence)
                projected_len = current_len + len(line)
                max_allowed = self._max_length - header_budget - close_cost(next_fence, [line])
                if projected_len <= max_allowed:
                    current_parts.append(line)
                    current_len = projected_len
                    open_fence = next_fence
                    continue

            # Single line exceeds chunk budget: slice it incrementally.
            # Preserve any trailing newline separately so chunks stay balanced.
            has_newline = line.endswith("\n")
            line_content = line[:-1] if has_newline else line
            line_idx = 0

            # If this line itself toggled a fence on, open the fence cleanly first.
            if is_fence_toggle and open_fence is None:
                open_fence = stripped
                line_idx = len(line_content)

            while line_idx < len(line_content):
                reserve_close = 4 if open_fence is not None else 0
                avail = self._max_length - header_budget - current_len - reserve_close
                if avail <= 1:
                    flush_current(reopen_fence=open_fence)
                    avail = self._max_length - header_budget - current_len - reserve_close
                    avail = max(avail, 1)

                slice_end = min(line_idx + avail, len(line_content))
                if slice_end < len(line_content):
                    space_pos = line_content.rfind(" ", line_idx + 1, slice_end + 1)
                    if space_pos > line_idx:
                        slice_end = space_pos + 1

                segment = line_content[line_idx:slice_end]
                current_parts.append(segment)
                current_len += len(segment)
                line_idx = slice_end

                if line_idx < len(line_content):
                    flush_current(reopen_fence=open_fence)

            if has_newline:
                if current_len + 1 + close_cost(next_fence, ["\n"]) > self._max_length - header_budget:
                    flush_current(reopen_fence=open_fence)
                current_parts.append("\n")
                current_len += 1

            open_fence = next_fence

        if current_parts:
            body = "".join(current_parts)
            # Only append a closing fence if caller content already exceeded chunking or left unclosed?
            # Actually if we already split into multiple chunks and open_fence is set, close cleanly.
            if open_fence is not None and chunks:
                tail_close = "```" if body.endswith("\n") else "\n```"
                if len(body) + len(tail_close) <= self._max_length - header_budget:
                    body += tail_close
            chunks.append(body)

        return chunks
