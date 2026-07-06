"""Streamlit dashboard for the email support agent."""

import streamlit as st
from loguru import logger

import config
from agent.graph import build_graph
from utils.mock_loader import load_mock_emails

config.setup_logging()

# Category metadata: label, color, order on the dashboard.
CATEGORIES = {
    "urgent": {"label": "Urgent", "color": "#E24B4A", "order": 0},
    "reply_needed": {"label": "Reply needed", "color": "#EF9F27", "order": 1},
    "info": {"label": "Info", "color": "#378ADD", "order": 2},
    "newsletter": {"label": "Newsletter", "color": "#639922", "order": 3},
    "spam": {"label": "Spam", "color": "#5F5E5A", "order": 4},
}


@st.cache_resource
def get_graph():
    """Builds the agent graph once per session and reuses it."""
    return build_graph()


def process_emails() -> tuple[list[dict], int]:
    """Runs every mock email through the graph with a live progress bar.

    A single failing email is logged and skipped, it never aborts the run.
    Returns the results and the number of failed emails.
    """
    graph = get_graph()
    emails = load_mock_emails()

    results: list[dict] = []
    failed = 0
    progress = st.progress(0.0, text="Starting triage...")

    for i, email in enumerate(emails, start=1):
        progress.progress(
            i / len(emails),
            text=f"Processing {i}/{len(emails)}: {email.subject[:50]}",
        )
        try:
            results.append(graph.invoke({"email": email}))
        except Exception as e:
            failed += 1
            logger.error(f"Processing failed for email id='{email.id}': {e}")

    progress.empty()
    return results, failed


def group_by_category(results: list[dict]) -> dict[str, list[dict]]:
    """Groups triaged emails into buckets keyed by category."""
    buckets: dict[str, list[dict]] = {cat: [] for cat in CATEGORIES}
    for r in results:
        category = r.get("category")
        if category in buckets:
            buckets[category].append(r)
    return buckets


def render_tile(category: str, count: int) -> None:
    """Renders a single category tile with a button to open it."""
    meta = CATEGORIES[category]

    st.markdown(
        f"""
        <div style="
            background-color: {meta['color']};
            border-radius: 12px;
            padding: 28px 24px;
            margin-bottom: 8px;
            min-height: 130px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        ">
            <div style="color: white; font-size: 20px; font-weight: 600;">
                {meta['label']}
            </div>
            <div style="color: white; font-size: 44px; font-weight: 700;">
                {count}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button(f"Open {meta['label']}", key=f"open_{category}", use_container_width=True):
        st.session_state["selected_category"] = category
        st.rerun()


def render_email_detail(r: dict) -> None:
    """Renders one triaged email with its draft inside a category view."""
    email = r["email"]

    st.markdown(f"**{email.subject}**")
    st.caption(f"From: {email.sender}  ·  Priority P{r['priority']}")

    if r.get("priority_reason"):
        st.caption(f"! {r['priority_reason']}")
    if r.get("degraded"):
        st.caption("!! Fallback values used for this email (see logs)")

    with st.expander("View full email"):
        st.write(email.body if email.body.strip() else "*(empty body)*")

    if r.get("draft_reply"):
        with st.expander("View draft reply"):
            st.write(r["draft_reply"])

    st.divider()


# --- Page setup ---
st.set_page_config(page_title="Email Support Agent", page_icon="📧", layout="wide")
st.title("Email Support Agent")
st.caption("Local LLM-powered email triage and reply drafting using LangGraph + Ollama")


# --- Top action bar ---
col_run, col_clear, _ = st.columns([2, 2, 6])
with col_run:
    if st.button("Run triage on inbox", type="primary", use_container_width=True):
        results, failed = process_emails()
        st.session_state["results"] = results
        st.session_state["failed"] = failed
        st.session_state.pop("selected_category", None)

with col_clear:
    if st.button("Clear session", use_container_width=True):
        st.session_state.pop("results", None)
        st.session_state.pop("failed", None)
        st.session_state.pop("selected_category", None)
        st.rerun()


# --- Main content ---
if "results" not in st.session_state:
    st.info("Click 'Run triage on inbox' to start.")

else:
    results = st.session_state["results"]
    buckets = group_by_category(results)

    if st.session_state.get("failed"):
        st.warning(f"{st.session_state['failed']} email(s) failed processing, see logs.")

    # A category is open -> show its emails.
    if st.session_state.get("selected_category"):
        category = st.session_state["selected_category"]
        meta = CATEGORIES[category]

        if st.button("← Back to dashboard"):
            st.session_state.pop("selected_category", None)
            st.rerun()

        st.subheader(f"{meta['label']}  ({len(buckets[category])})")

        if not buckets[category]:
            st.write("No emails in this category.")
        else:
            sorted_emails = sorted(
                buckets[category], key=lambda r: r["priority"] or 0, reverse=True
            )
            for r in sorted_emails:
                render_email_detail(r)

    # No category open -> show the tile dashboard.
    else:
        st.subheader(f"Triaged {len(results)} emails")

        ordered = sorted(CATEGORIES.items(), key=lambda kv: kv[1]["order"])
        cols = st.columns(3)
        for i, (category, _meta) in enumerate(ordered):
            with cols[i % 3]:
                render_tile(category, len(buckets[category]))
