"""Content Strategy Agent - long-term content memory powered by Hindsight.

Run (light theme recommended):
  streamlit run app.py --server.fileWatcherType none --theme.base light

Hindsight Cloud:  HINDSIGHT_URL=https://api.hindsight.vectorize.io  HINDSIGHT_API_KEY=hsk_...
Local embedded:   USE_EMBEDDED=1  LLM_PROVIDER / LLM_MODEL / LLM_API_KEY
Optional:         BANK_ID=acme-demo  (use a fresh bank for a clean before/after recording)
"""
import os
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import pandas as pd
import streamlit as st
from hindsight_client import Hindsight

from seed_data import NEW_POST, POSTS, to_text

BANK = os.getenv("BANK_ID", "acme-content")
URL = os.getenv("HINDSIGHT_URL", "http://localhost:8888")
EMBEDDED = os.getenv("USE_EMBEDDED") == "1" and not os.getenv("HINDSIGHT_API_KEY")

st.set_page_config(page_title="Content Strategy Agent", page_icon="🧠", layout="wide")

# ----------------------------------------------------------------------------
# Styling
# ----------------------------------------------------------------------------
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Newsreader:wght@500;600&family=Source+Sans+3:wght@400;500;600&display=swap');

:root {
  --ink: #12203A;
  --muted: #5A6A80;
  --surface: #FFFFFF;
  --line: #DCE3EC;
  --navy: #0B1B34;
  --deep: #0F4C5C;
  --teal: #0F766E;
  --mint: #5EEAD4;
  --indigo: #3B5BDB;
  --cyan: #0E7490;
  --amber: #D97706;
  --amber-soft: #FDF1DC;
}

/* ---------- keyframes ---------- */
@keyframes rise     { from { opacity: 0; transform: translateY(14px); } to { opacity: 1; transform: translateY(0); } }
@keyframes fade     { from { opacity: 0; } to { opacity: 1; } }
@keyframes drift    { 0% { transform: translate(0,0) scale(1); } 50% { transform: translate(40px,-24px) scale(1.12); } 100% { transform: translate(0,0) scale(1); } }
@keyframes drift2   { 0% { transform: translate(0,0) scale(1); } 50% { transform: translate(-46px,20px) scale(1.18); } 100% { transform: translate(0,0) scale(1); } }
@keyframes grade    { 0% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } 100% { background-position: 0% 50%; } }
@keyframes ripple   { 0% { box-shadow: 0 0 0 0 rgba(94,234,212,.55); } 70% { box-shadow: 0 0 0 10px rgba(94,234,212,0); } 100% { box-shadow: 0 0 0 0 rgba(94,234,212,0); } }
@keyframes glow     { 0%,100% { box-shadow: 0 0 0 0 rgba(217,119,6,0); } 50% { box-shadow: 0 0 0 6px rgba(217,119,6,.16); } }
@keyframes breathe  { 0%,100% { opacity: .55; } 50% { opacity: 1; } }
@keyframes sheen    { from { transform: translateX(-120%); } to { transform: translateX(120%); } }

/* ---------- page: cool at the top, a touch of warmth at the bottom ---------- */
.stApp {
  background: linear-gradient(180deg, #E6EEF5 0%, #F2F5F9 34%, #F6F4EF 100%);
  color: var(--ink);
  font-family: 'Source Sans 3', system-ui, sans-serif;
}
.stApp p, .stApp li, .stApp label, .stApp span, .stApp div { color: inherit; }
h1, h2, h3, h4 { font-family: 'Newsreader', Georgia, serif !important; color: var(--ink) !important; letter-spacing: -0.01em; }
h3 { font-size: 1.35rem !important; }

[data-testid="stToolbar"], .stAppDeployButton, #MainMenu, footer { display: none !important; }
.block-container { padding-top: 1.6rem; max-width: 1280px; }

/* ---------- sidebar ---------- */
[data-testid="stSidebar"] { background: var(--surface); border-right: 1px solid var(--line); }
[data-testid="stSidebar"] > div:first-child { border-top: 4px solid transparent;
  border-image: linear-gradient(90deg, var(--navy), var(--teal), var(--mint)) 1; }
[data-testid="stSidebar"] * { color: var(--ink); }

/* ---------- hero: graded navy -> deep teal -> teal, with slow drifting light ---------- */
.hero {
  position: relative; overflow: hidden; border-radius: 18px; padding: 2.1rem 2.4rem 1.9rem 2.4rem; margin-bottom: 1.4rem;
  background: linear-gradient(115deg, #0B1B34 0%, #0F3B52 38%, #0F766E 78%, #14958A 100%);
  background-size: 220% 220%; animation: grade 22s ease-in-out infinite, fade .6s ease both;
  box-shadow: 0 18px 40px -22px rgba(11,27,52,.65);
}
.hero .orb { position: absolute; border-radius: 50%; filter: blur(46px); pointer-events: none; }
.hero .orb.a { width: 280px; height: 280px; right: -60px; top: -90px; background: rgba(94,234,212,.42); animation: drift 14s ease-in-out infinite; }
.hero .orb.b { width: 220px; height: 220px; right: 22%; bottom: -120px; background: rgba(245,158,11,.30); animation: drift2 17s ease-in-out infinite; }
.hero h1 { position: relative; font-size: 2.7rem; line-height: 1.1; margin: 0 0 .6rem 0; color: #FFFFFF !important; animation: rise .7s .05s ease both; }
.hero p  { position: relative; font-size: 1.1rem; color: #CFE6EA !important; max-width: 60ch; margin: 0; line-height: 1.55; animation: rise .7s .18s ease both; }
.status  { position: relative; display: inline-flex; align-items: center; gap: .55rem; margin-top: 1.1rem; padding: .32rem .85rem;
  border: 1px solid rgba(255,255,255,.28); border-radius: 999px; background: rgba(255,255,255,.12);
  backdrop-filter: blur(6px); font-size: .86rem; color: #E3F7F4 !important; animation: rise .7s .3s ease both; }
.dot { width: 9px; height: 9px; border-radius: 50%; background: var(--mint); display: inline-block; animation: ripple 2.2s ease-out infinite; }

/* ---------- metrics: each card gets its own accent from the grade ---------- */
[data-testid="stMetric"] {
  position: relative; overflow: hidden; background: var(--surface); border: 1px solid var(--line); border-radius: 12px;
  padding: 1rem 1.15rem .9rem 1.15rem; border-top: 3px solid var(--teal);
  animation: rise .6s ease both; transition: transform .25s ease, box-shadow .25s ease;
}
[data-testid="stMetric"]:hover { transform: translateY(-4px); box-shadow: 0 14px 26px -16px rgba(18,32,58,.38); }
[data-testid="stMetric"]::after { content: ""; position: absolute; inset: 0; width: 40%; pointer-events: none;
  background: linear-gradient(100deg, transparent, rgba(255,255,255,.65), transparent); transform: translateX(-120%); }
[data-testid="stMetric"]:hover::after { animation: sheen .9s ease; }
[data-testid="stColumn"]:nth-child(1) [data-testid="stMetric"], [data-testid="column"]:nth-child(1) [data-testid="stMetric"] { border-top-color: var(--teal);   animation-delay: .05s; }
[data-testid="stColumn"]:nth-child(2) [data-testid="stMetric"], [data-testid="column"]:nth-child(2) [data-testid="stMetric"] { border-top-color: var(--cyan);   animation-delay: .15s; }
[data-testid="stColumn"]:nth-child(3) [data-testid="stMetric"], [data-testid="column"]:nth-child(3) [data-testid="stMetric"] { border-top-color: var(--indigo); animation-delay: .25s; }
[data-testid="stColumn"]:nth-child(4) [data-testid="stMetric"], [data-testid="column"]:nth-child(4) [data-testid="stMetric"] { border-top-color: var(--amber);  animation-delay: .35s; }
[data-testid="stMetricLabel"] p { color: var(--muted) !important; font-size: .9rem; }
[data-testid="stMetricValue"] { font-family: 'Newsreader', Georgia, serif; font-size: 2.05rem; color: var(--ink); }

/* ---------- tabs ---------- */
.stTabs [data-baseweb="tab-list"] { gap: 1.7rem; border-bottom: 1px solid var(--line); }
.stTabs [data-baseweb="tab"] { padding: .65rem .1rem; font-weight: 600; color: var(--muted); transition: color .2s ease; }
.stTabs [data-baseweb="tab"]:hover { color: var(--teal); }
.stTabs [aria-selected="true"] { color: var(--teal) !important; }
.stTabs [data-baseweb="tab-highlight"] { background: linear-gradient(90deg, var(--teal), var(--mint)) !important; height: 3px !important; }
.stTabs [data-baseweb="tab-panel"] { animation: fade .45s ease both; }

/* ---------- buttons ---------- */
.stButton > button, [data-testid="stFormSubmitButton"] > button {
  border-radius: 9px; border: 1px solid var(--line); background: var(--surface); color: var(--ink); font-weight: 600;
  transition: transform .2s ease, box-shadow .2s ease, border-color .2s ease, background-position .4s ease;
}
.stButton > button:hover, [data-testid="stFormSubmitButton"] > button:hover { border-color: var(--teal); color: var(--teal); transform: translateY(-2px); box-shadow: 0 10px 20px -14px rgba(15,118,110,.7); }
.stButton > button:active, [data-testid="stFormSubmitButton"] > button:active { transform: translateY(0); }
.stButton > button[kind="primary"], [data-testid="stFormSubmitButton"] > button[kind="primary"] {
  color: #fff; border-color: transparent; background: linear-gradient(110deg, #0F766E 0%, #0E8F86 50%, #0F766E 100%); background-size: 200% 100%;
}
.stButton > button[kind="primary"]:hover, [data-testid="stFormSubmitButton"] > button[kind="primary"]:hover { color: #fff; background-position: 100% 0; }

/* ---------- results ---------- */
[data-testid="stVerticalBlockBorderWrapper"] { background: var(--surface); border-radius: 14px; animation: rise .5s ease both; }
.result-note { color: var(--muted); font-size: .85rem; margin-bottom: .4rem; }
.learned { background: var(--amber-soft); border-left: 3px solid var(--amber); padding: .55rem .85rem; border-radius: 8px; font-size: .92rem; animation: glow 2.6s ease-in-out 3; }
.mem { padding: .55rem 0; border-bottom: 1px solid var(--line); line-height: 1.45; }

/* ---------- loading states ---------- */
[data-testid="stSpinner"] { animation: breathe 1.4s ease-in-out infinite; }
[data-testid="stProgress"] [role="progressbar"] > div > div { background: linear-gradient(90deg, var(--teal), var(--mint)) !important; }
[data-testid="stAlert"] { border-radius: 12px; animation: rise .4s ease both; }

/* ---------- respect reduced-motion settings ---------- */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation: none !important; transition: none !important; }
}
</style>
""",
    unsafe_allow_html=True,
)


# ----------------------------------------------------------------------------
# Hindsight client (one long-lived worker thread; see notes in README)
# ----------------------------------------------------------------------------
class ThreadedClient:
    """Run every Hindsight call on one persistent thread so the client's HTTP session
    always uses the same event loop, never the one Streamlit already runs."""

    def __init__(self, client):
        self._c = client
        self._ex = ThreadPoolExecutor(max_workers=1, thread_name_prefix="hindsight")

    def __getattr__(self, name):
        attr = getattr(self._c, name)
        if not callable(attr):
            return attr

        def run(*args, **kwargs):
            return self._ex.submit(attr, *args, **kwargs).result()

        return run


@st.cache_resource
def get_client():
    if EMBEDDED:
        from hindsight import HindsightServer

        server = HindsightServer(
            llm_provider=os.getenv("LLM_PROVIDER", "openai"),
            llm_model=os.getenv("LLM_MODEL", "gpt-5-mini"),
            llm_api_key=os.environ["LLM_API_KEY"],
        )
        server.__enter__()
        return ThreadedClient(Hindsight(base_url=server.url))
    api_key = os.getenv("HINDSIGHT_API_KEY")
    kwargs = {"api_key": api_key} if api_key else {}
    return ThreadedClient(Hindsight(base_url=URL, **kwargs))


def as_text(resp):
    """Be defensive about response shapes across client versions."""
    for attr in ("text", "answer", "content", "response"):
        val = getattr(resp, attr, None)
        if isinstance(val, str) and val.strip():
            return val
    if isinstance(resp, dict):
        for key in ("text", "answer", "content", "response"):
            if resp.get(key):
                return resp[key]
    return str(resp)


def call_with_retry(fn, attempts=6, **kwargs):
    """Retry temporary provider errors (503 overloaded, 429 rate limit) with backoff."""
    for i in range(attempts):
        try:
            return fn(**kwargs)
        except Exception as e:
            msg = str(e)
            temporary = any(k in msg for k in ("503", "UNAVAILABLE", "429", "RESOURCE_EXHAUSTED", "high demand"))
            if temporary and i < attempts - 1:
                time.sleep(5 * (i + 1))
                continue
            raise


def friendly(e):
    msg = str(e)
    if "401" in msg or "403" in msg:
        return "Hindsight or the model provider rejected the API key. Check HINDSIGHT_API_KEY (or LLM_API_KEY) and restart."
    if "429" in msg or "RESOURCE_EXHAUSTED" in msg:
        return "The model provider's rate limit or quota is used up. Wait a minute and try again."
    if "503" in msg or "UNAVAILABLE" in msg:
        return "The model provider is busy right now. Try again in a minute."
    return f"Something went wrong: {msg[:300]}"


def retain(client, post):
    call_with_retry(
        client.retain,
        bank_id=BANK,
        content=to_text(post),
        context="content calendar and performance",
        timestamp=f"{post[0]}T09:00:00Z",
    )


# ----------------------------------------------------------------------------
# Session state
# ----------------------------------------------------------------------------
ss = st.session_state
ss.setdefault("posts", list(POSTS))  # local copy, used only for the charts and numbers
ss.setdefault("loaded", 0)
ss.setdefault("seeded", False)
ss.setdefault("runs", {})  # analysis key -> list of runs, so we can compare before and after
ss.setdefault("learned", [])  # titles added during this session

client = get_client()


def posts_df():
    df = pd.DataFrame(ss.posts, columns=["date", "format", "title", "topic", "voice", "views", "shares"])
    df["date"] = pd.to_datetime(df["date"])
    return df


# ----------------------------------------------------------------------------
# Sidebar
# ----------------------------------------------------------------------------
with st.sidebar:
    st.caption("UI version: animated v3")
    st.markdown("### Memory")
    where = "Local embedded server" if EMBEDDED else URL
    st.caption(f"Server: {where}")
    st.caption(f"Memory bank: {BANK}")

    already = st.checkbox("Sample posts are already in this bank", value=ss.seeded)
    if already:
        ss.seeded = True

    if st.button("Load 18 sample posts", disabled=ss.seeded, use_container_width=True):
        progress = st.progress(0.0, text="Starting...")
        start = ss.get("loaded", 0)
        try:
            for idx in range(start, len(POSTS)):
                retain(client, POSTS[idx])
                ss.loaded = idx + 1
                progress.progress((idx + 1) / len(POSTS), text=f"Retained {idx + 1} of {len(POSTS)}")
            ss.seeded = True
            st.success("Sample posts loaded.")
        except Exception as e:
            st.error(friendly(e))
            st.caption("Click the button again to continue from where it stopped.")

    st.divider()
    st.markdown("### Publish a new post")
    st.caption("Add a post the agent hasn't seen. It retains it, and later answers can use it.")
    with st.form("new_post"):
        title = st.text_input("Title", NEW_POST[2])
        c1, c2 = st.columns(2)
        fmt = c1.selectbox("Format", ["blog", "video", "linkedin", "twitter", "whitepaper"])
        date = c2.text_input("Date", NEW_POST[0])
        topic = st.text_input("Topic", NEW_POST[3])
        voice = st.text_input("Voice", NEW_POST[4])
        c3, c4 = st.columns(2)
        views = c3.number_input("Views", value=NEW_POST[5], step=100)
        shares = c4.number_input("Shares", value=NEW_POST[6], step=10)
        submitted = st.form_submit_button("Publish and let the agent learn", type="primary", use_container_width=True)
    if submitted:
        with st.spinner("Retaining..."):
            try:
                post = (date, fmt, title, topic, voice, int(views), int(shares))
                retain(client, post)
                ss.posts.append(post)
                ss.learned.append(title)
                st.success("Retained. Give it a minute, then run an analysis again.")
            except Exception as e:
                st.error(friendly(e))

    if ss.learned:
        st.divider()
        st.markdown("### Learned this session")
        for t in ss.learned:
            st.markdown(f'<div class="learned">{t}</div>', unsafe_allow_html=True)


# ----------------------------------------------------------------------------
# Hero and numbers
# ----------------------------------------------------------------------------
st.markdown(
    f"""
<div class="hero">
  <div class="orb a"></div><div class="orb b"></div>
  <h1>What has our content taught us?</h1>
  <p>A content strategy agent with long-term memory. It remembers every post you published and how it performed, then tells you what to make next.</p>
  <span class="status"><span class="dot"></span>Memory connected, bank {BANK}</span>
</div>
""",
    unsafe_allow_html=True,
)

df = posts_df()
by_format = df.groupby("format")["views"].mean().round().sort_values(ascending=False)
share_rate = df["shares"].sum() / max(df["views"].sum(), 1) * 1000

m1, m2, m3, m4 = st.columns(4)
m1.metric("Posts in memory", len(df))
m2.metric("Total views", f"{int(df['views'].sum()):,}")
m3.metric("Shares per 1,000 views", f"{share_rate:.1f}")
m4.metric("Best format by average views", by_format.index[0] if len(by_format) else "none")

ch1, ch2 = st.columns(2)
with ch1:
    st.markdown("### Average views by format")
    st.bar_chart(by_format, color="#0F766E", height=240)
with ch2:
    st.markdown("### Views over time")
    st.line_chart(df.set_index("date")["views"].sort_index(), color="#0E7490", height=240)

st.markdown("&nbsp;", unsafe_allow_html=True)


# ----------------------------------------------------------------------------
# Analyses
# ----------------------------------------------------------------------------
def analysis_panel(key, button_label, query, spinner_text):
    if st.button(button_label, key=f"btn_{key}", type="primary"):
        with st.spinner(spinner_text):
            try:
                r = call_with_retry(client.reflect, bank_id=BANK, query=query)
                ss.runs.setdefault(key, []).append(
                    {"time": datetime.now().strftime("%H:%M:%S"), "text": as_text(r), "posts": len(ss.posts)}
                )
            except Exception as e:
                st.error(friendly(e))

    runs = ss.runs.get(key, [])
    if not runs:
        st.info(f"Press the button above. The agent will read your memory and write this analysis.")
        return

    latest = runs[-1]
    with st.container(border=True):
        st.markdown(
            f'<div class="result-note">Run at {latest["time"]}, with {latest["posts"]} posts known to this session</div>',
            unsafe_allow_html=True,
        )
        st.markdown(latest["text"])

    if len(runs) > 1:
        prev = runs[-2]
        with st.expander("Compare with the previous run", expanded=False):
            left, right = st.columns(2)
            with left:
                st.markdown(f"**Before** (run at {prev['time']}, {prev['posts']} posts)")
                st.markdown(prev["text"])
            with right:
                st.markdown(f"**After** (run at {latest['time']}, {latest['posts']} posts)")
                st.markdown(latest["text"])


def dedupe(texts):
    seen, out = set(), []
    for t in texts:
        key = t.split("|")[0].strip().lower()
        if key not in seen:
            seen.add(key)
            out.append(t)
    return out


tab1, tab2, tab3, tab4 = st.tabs(["Coverage gaps", "Brand voice", "What to publish next", "Ask memory"])

with tab1:
    st.markdown("### Where are the gaps?")
    st.caption("Topics and formats that are over-used, under-used or missing, with the posts behind each claim.")
    analysis_panel(
        "gaps",
        "Find coverage gaps",
        "Based on everything we have published, which topics and formats are we under-covering or "
        "missing entirely, and which are over-saturated? Cite specific posts and metrics.",
        "Reading your whole content history...",
    )

with tab2:
    st.markdown("### How has our voice changed?")
    st.caption("Month by month, which voice performs best, and how we sound today.")
    analysis_panel(
        "voice",
        "Analyze brand voice",
        "How has our brand voice evolved over time, month by month? Which voice performs best and "
        "which performs worst? Describe our current voice in 3 sentences.",
        "Tracing your brand voice over time...",
    )

with tab3:
    st.markdown("### What should we publish next week?")
    st.caption("Three recommendations, each backed by posts from your own history.")
    analysis_panel(
        "next",
        "Recommend next week's content",
        "Recommend 3 pieces of content to publish next week. For each give topic, format, voice, and "
        "the evidence from our past performance justifying it.",
        "Planning next week's content...",
    )

with tab4:
    st.markdown("### Ask your memory")
    st.caption("Ask about any post, topic or result. Try asking about something you haven't published yet, then publish it and ask again.")
    q = st.text_input("Your question", "Have we published anything on security or prompt injection?")
    style = st.radio("Show me", ["Matching memories", "A written answer"], horizontal=True)
    if st.button("Search memory", type="primary"):
        with st.spinner("Searching..."):
            try:
                if style == "A written answer":
                    r = call_with_retry(client.reflect, bank_id=BANK, query=q)
                    with st.container(border=True):
                        st.markdown(as_text(r))
                else:
                    res = call_with_retry(client.recall, bank_id=BANK, query=q)
                    items = getattr(res, "results", res)
                    texts = dedupe([as_text(i) for i in items])
                    if not texts:
                        st.info("Nothing in memory matches that question yet.")
                    else:
                        learned = [t.lower() for t in ss.learned]
                        st.caption(f"{len(texts)} distinct memories found. The closest matches are first.")
                        with st.container(border=True):
                            for t in texts[:6]:
                                new = any(x in t.lower() for x in learned)
                                badge = ":orange-badge[Learned this session] " if new else ""
                                st.markdown(f"{badge}{t}")
                        if len(texts) > 6:
                            with st.expander(f"Show the other {len(texts) - 6}"):
                                for t in texts[6:]:
                                    st.markdown(f"- {t}")
            except Exception as e:
                st.error(friendly(e))
