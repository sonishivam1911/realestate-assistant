import json
import logging
import os
import uuid
from contextlib import contextmanager
from datetime import date
from typing import Any, Generator

import psycopg2
import psycopg2.extras

logger = logging.getLogger(__name__)


def _postgres_uri() -> str:
    return (
        os.getenv("POSTGRES_URI")
        or os.getenv("POSTGRES_URI_CONTABO")
        or os.getenv("POSTGRES_URI_HOMELAB")
        or os.getenv("DATABASE_URL", "")
    )


@contextmanager
def get_connection() -> Generator:
    uri = _postgres_uri()
    if not uri:
        raise ValueError(
            "Set POSTGRES_URI or POSTGRES_URI_CONTABO (Contabo homelab Postgres)"
        )
    conn = psycopg2.connect(uri)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def ensure_schema() -> None:
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    with open(schema_path) as f:
        sql = f.read()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
    logger.info("realestate schema applied")


def create_conversation(
    title: str | None = None,
    subject_address: str | None = None,
    radius_miles: float = 5.0,
    user_email: str | None = None,
) -> str:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO realestate.conversations
                    (title, subject_address, radius_miles, user_email)
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (title, subject_address, radius_miles, user_email),
            )
            return str(cur.fetchone()[0])


def get_conversation(conversation_id: str) -> dict | None:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT id, title, subject_address, user_email, radius_miles, status,
                       created_at, updated_at
                FROM realestate.conversations
                WHERE id = %s
                """,
                (conversation_id,),
            )
            row = cur.fetchone()
            return dict(row) if row else None


def update_conversation(
    conversation_id: str,
    *,
    title: str | None = None,
    status: str | None = None,
    user_email: str | None = None,
) -> dict | None:
    sets = []
    params: list = []
    if title is not None:
        sets.append("title = %s")
        params.append(title)
    if status is not None:
        sets.append("status = %s")
        params.append(status)
    if user_email is not None:
        sets.append("user_email = %s")
        params.append(user_email)
    if not sets:
        return get_conversation(conversation_id)

    params.append(conversation_id)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE realestate.conversations SET {', '.join(sets)} WHERE id = %s",
                params,
            )
    return get_conversation(conversation_id)


def delete_conversation(conversation_id: str) -> bool:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM realestate.conversations WHERE id = %s RETURNING id",
                (conversation_id,),
            )
            return cur.fetchone() is not None


def list_conversations(limit: int = 50) -> list[dict]:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT id, title, subject_address, user_email, radius_miles, status,
                       created_at, updated_at
                FROM realestate.conversations
                ORDER BY updated_at DESC
                LIMIT %s
                """,
                (limit,),
            )
            return [dict(r) for r in cur.fetchall()]


def get_messages(conversation_id: str) -> list[dict]:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT id, role, content, metadata, created_at
                FROM realestate.messages
                WHERE conversation_id = %s
                ORDER BY created_at ASC
                """,
                (conversation_id,),
            )
            return [dict(r) for r in cur.fetchall()]


def add_message(
    conversation_id: str,
    role: str,
    content: str,
    metadata: dict | None = None,
) -> str:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO realestate.messages (conversation_id, role, content, metadata)
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (conversation_id, role, content, json.dumps(metadata or {})),
            )
            msg_id = str(cur.fetchone()[0])
            cur.execute(
                "UPDATE realestate.conversations SET updated_at = now() WHERE id = %s",
                (conversation_id,),
            )
            return msg_id


def save_cma_run(conversation_id: str, message_id: str, state: dict[str, Any]) -> str:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO realestate.cma_runs (
                    conversation_id, message_id, status,
                    subject_property, geo, radius_miles, timeframe_months,
                    comp_research, market_pulse, macro_context, cma_report,
                    errors, completed_at
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                    CASE WHEN %s IN ('complete','failed') THEN now() ELSE NULL END)
                RETURNING id
                """,
                (
                    conversation_id,
                    message_id,
                    state.get("status", "complete"),
                    json.dumps(state.get("target_property", {})),
                    json.dumps(state.get("geo", {})),
                    state.get("radius_miles"),
                    state.get("timeframe_months"),
                    json.dumps(state.get("comp_research")) if state.get("comp_research") else None,
                    json.dumps(state.get("market_pulse")) if state.get("market_pulse") else None,
                    json.dumps(state.get("macro_context")) if state.get("macro_context") else None,
                    json.dumps(state.get("cma_report")) if state.get("cma_report") else None,
                    json.dumps(state.get("errors", [])),
                    state.get("status"),
                ),
            )
            run_id = str(cur.fetchone()[0])

            for branch, key in [
                ("comps", "comp_citations"),
                ("market", "market_citations"),
                ("macro", "macro_citations"),
            ]:
                for cite in state.get(key) or []:
                    cur.execute(
                        """
                        INSERT INTO realestate.citations (cma_run_id, branch, url, title, snippet)
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (
                            run_id,
                            branch,
                            cite.get("url", ""),
                            cite.get("title"),
                            cite.get("content"),
                        ),
                    )

            for comp in (state.get("comp_research") or {}).get("comps") or []:
                sold = comp.get("sold_date")
                if isinstance(sold, str) and sold:
                    try:
                        sold_date = date.fromisoformat(sold[:10])
                    except ValueError:
                        sold_date = None
                else:
                    sold_date = None

                cur.execute(
                    """
                    INSERT INTO realestate.comparables (
                        cma_run_id, address, sold_date, sold_price, sqft,
                        bedrooms, bathrooms, price_per_sqft, distance_miles,
                        property_type, source_url, source_name
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (
                        run_id,
                        comp.get("address", ""),
                        sold_date,
                        comp.get("sold_price"),
                        comp.get("sqft"),
                        comp.get("bedrooms"),
                        comp.get("bathrooms"),
                        comp.get("price_per_sqft"),
                        comp.get("distance_miles"),
                        comp.get("property_type"),
                        comp.get("source_url"),
                        comp.get("source_name"),
                    ),
                )

            return run_id


def mark_cma_email_sent(run_id: str) -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE realestate.cma_runs SET email_sent_at = now() WHERE id = %s",
                (run_id,),
            )
