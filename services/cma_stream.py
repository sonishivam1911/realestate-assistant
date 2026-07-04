"""Stream CMA workflow through Vercel AI SDK UIMessageStream protocol."""

import asyncio
import logging
import os
from typing import Any

from ai_sdk_stream_python import StreamContext

from services.email_service import is_valid_email, send_cma_report, smtp_configured
from workflow.cma_graph import CMAGraph

logger = logging.getLogger(__name__)


def _extract_text_from_message(message: dict[str, Any]) -> str:
    parts = message.get("parts") or []
    if parts:
        return "".join(
            p.get("text", "") for p in parts if p.get("type") == "text"
        )
    return message.get("content") or ""


def _extract_user_message(messages: list[dict[str, Any]]) -> str:
    for message in reversed(messages):
        if message.get("role") == "user":
            return _extract_text_from_message(message).strip()
    return ""


async def stream_cma_chat(
    *,
    messages: list[dict[str, Any]],
    conversation_id: str | None,
    radius_miles: float,
    user_email: str | None,
    email_delivery_enabled: bool = True,
    ctx: StreamContext,
) -> None:
    if email_delivery_enabled and (not user_email or not is_valid_email(user_email)):
        await ctx.write_text(
            "Please add your **email address** in **Settings** and enable "
            "**Email me chat reports** before requesting a CMA."
        )
        return

    user_text = _extract_user_message(messages)
    if not user_text:
        await ctx.write_text("Please provide a property address for the CMA.")
        return

    cid = await _ensure_conversation(
        conversation_id, user_text, radius_miles, user_email or ""
    )
    if user_email and is_valid_email(user_email):
        await _update_conversation_email(cid, user_email)
    await _save_user_message(cid, user_text)

    await ctx.write_reasoning(
        f"Starting CMA — {radius_miles}mi radius, 3-month comps."
        + (f" Reports → {user_email}" if email_delivery_enabled and user_email else "")
    )
    await ctx.new_step()
    await ctx.write_reasoning("Step 1/3: Intake — parsing address and geocoding…")

    graph = CMAGraph()
    state = await asyncio.to_thread(
        graph.run,
        user_text,
        conversation_id=cid,
        radius_miles=radius_miles,
    )

    if state.get("status") == "failed":
        for err in state.get("errors") or ["Unknown error"]:
            await ctx.write_text(f"\n\n**Error:** {err}\n")
        return

    await ctx.new_step()
    await ctx.write_reasoning(
        "Step 2/3: Parallel research — comps, market pulse, macro (fan-out)."
    )

    report = state.get("cma_report") or {}
    markdown = (
        report.get("markdown_report")
        or report.get("executive_summary")
        or state.get("assistant_message")
        or "Analysis complete."
    )

    await ctx.new_step()
    await ctx.write_reasoning("Step 3/3: Writing client-ready CMA report…")
    await ctx.new_step()

    chunk_size = int(os.getenv("CMA_STREAM_CHUNK_SIZE", "120"))
    for i in range(0, len(markdown), chunk_size):
        await ctx.write_text(markdown[i : i + chunk_size])
        await asyncio.sleep(0.01)

    for cite in state.get("all_citations") or []:
        url = cite.get("url", "")
        if url:
            await ctx.write_source(url, url, cite.get("title") or url)

    run_id = await _save_assistant_run(
        cid, state, markdown, user_email or ""
    )

    if not email_delivery_enabled or not user_email or not is_valid_email(user_email):
        return

    subject = state.get("target_property", {}).get("address") or user_text
    price = report.get("recommended_list_price")
    price_str = f"${price:,.0f}" if isinstance(price, (int, float)) else None

    sent = await asyncio.to_thread(
        send_cma_report,
        to_email=user_email,
        subject_property=subject,
        report_markdown=markdown,
        recommended_price=price_str,
    )

    if sent and run_id:
        await asyncio.to_thread(_mark_email_sent, run_id)
        await ctx.write_text(
            f"\n\n---\n📧 **Report sent to {user_email}**"
        )
    elif smtp_configured():
        await ctx.write_text(
            f"\n\n---\n⚠️ Could not send email to {user_email}. "
            "Your report is saved above — try again or contact support."
        )
    else:
        await ctx.write_text(
            f"\n\n---\n📧 Report ready for **{user_email}** "
            "(email delivery not configured on server — copy from above)."
        )


async def _ensure_conversation(
    conversation_id: str | None,
    user_text: str,
    radius_miles: float,
    user_email: str,
) -> str:
    if conversation_id:
        return conversation_id
    try:
        from db.client import create_conversation

        return create_conversation(
            title=user_text[:80],
            subject_address=user_text,
            radius_miles=radius_miles,
            user_email=user_email,
        )
    except Exception as e:
        logger.warning("Conversation create skipped: %s", e)
        return ""


async def _update_conversation_email(conversation_id: str, user_email: str) -> None:
    if not conversation_id:
        return
    try:
        from db.client import update_conversation

        update_conversation(conversation_id, user_email=user_email)
    except Exception as e:
        logger.warning("Email update skipped: %s", e)


async def _save_user_message(conversation_id: str, user_text: str) -> None:
    if not conversation_id:
        return
    try:
        from db.client import add_message

        add_message(conversation_id, "user", user_text)
    except Exception as e:
        logger.warning("User message persist skipped: %s", e)


async def _save_assistant_run(
    conversation_id: str,
    state: dict[str, Any],
    assistant_text: str,
    user_email: str,
) -> str:
    if not conversation_id:
        return ""
    try:
        from db.client import add_message, save_cma_run

        msg_id = add_message(
            conversation_id,
            "assistant",
            assistant_text,
            metadata={
                "status": state.get("status"),
                "user_email": user_email,
                "recommended_price": (state.get("cma_report") or {}).get(
                    "recommended_list_price"
                ),
            },
        )
        return save_cma_run(conversation_id, msg_id, state)
    except Exception as e:
        logger.warning("Assistant persist skipped: %s", e)
        return ""


def _mark_email_sent(run_id: str) -> None:
    from db.client import mark_cma_email_sent

    mark_cma_email_sent(run_id)
