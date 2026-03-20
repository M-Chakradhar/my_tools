import streamlit as st
import requests
import json
from datetime import datetime, timezone

# ── Config ────────────────────────────────────────────────────────────────────

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/html,*/*;q=0.9",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://www.reddit.com/",
    "DNT": "1",
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def to_json_url(url: str) -> str:
    url = url.strip().rstrip("/")
    if "?" in url:
        url = url.split("?")[0].rstrip("/")
    if not url.endswith(".json"):
        url += ".json"
    return url

def fmt_ts(unix: float) -> str:
    return datetime.fromtimestamp(unix, tz=timezone.utc).strftime("%Y-%m-%d")

def fetch_reddit(url: str) -> list:
    import time
    session = requests.Session()
    session.headers.update(HEADERS)
    time.sleep(1.5)
    resp = session.get(to_json_url(url), timeout=12)
    resp.raise_for_status()
    return resp.json()

def flatten_comments(children: list, depth: int = 0) -> list:
    """Recursively flatten all comment nodes into a flat list with depth info."""
    results = []
    for item in children:
        if item.get("kind") != "t1":
            continue
        d = item["data"]
        body = d.get("body", "").strip()
        if body in ("[deleted]", "[removed]", ""):
            continue
        results.append({
            "depth": depth,
            "score": d.get("score", 0),
            "body": body,
            "created": fmt_ts(d.get("created_utc", 0)),
        })
        replies = d.get("replies")
        if replies and isinstance(replies, dict):
            sub = replies.get("data", {}).get("children", [])
            results.extend(flatten_comments(sub, depth + 1))
    return results

# ── Markdown builders ─────────────────────────────────────────────────────────

def build_post_md(post: dict) -> str:
    lines = [
        f"# {post['title']}",
        "",
        f"**Subreddit:** r/{post['subreddit']}",
        f"**Upvotes:** {post['score']:,}  |  **Upvote ratio:** {int(post['upvote_ratio'] * 100)}%",
        f"**Total comments:** {post['num_comments']:,}",
        f"**Posted:** {fmt_ts(post['created_utc'])}",
        f"**Source:** https://reddit.com{post['permalink']}",
        "",
        "---",
        "",
    ]
    body = post.get("selftext", "").strip()
    if body and body not in ("[removed]", "[deleted]"):
        lines += ["## Post body", "", body, ""]
    else:
        lines += ["## Post body", "", "_This post has no text body (link post or removed)._", ""]
    return "\n".join(lines)

def build_comments_md(comments: list, max_comments: int) -> str:
    sorted_comments = sorted(comments, key=lambda c: c["score"], reverse=True)
    selected = sorted_comments[:max_comments]

    lines = [
        f"# Comments ({len(selected)} of {len(comments)} total, sorted by upvotes)",
        "",
        "_Usernames removed. Sorted highest upvotes first._",
        "",
        "---",
        "",
    ]
    for i, c in enumerate(selected, 1):
        indent_label = "Top-level" if c["depth"] == 0 else f"Reply (depth {c['depth']})"
        lines += [
            f"## Comment {i}  ·  {c['score']:,} upvotes  ·  {indent_label}",
            "",
            c["body"],
            "",
            "---",
            "",
        ]
    return "\n".join(lines)

# ── UI ────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Reddit → Script Scraper",
    page_icon="🎬",
    layout="centered",
)

st.title("🎬 Reddit → Script Scraper")
st.caption(
    "Paste a Reddit post URL. Get two clean `.md` files — post details and top comments — "
    "ready to drop into any AI to generate a YouTube script."
)

st.divider()

url = st.text_input(
    "Reddit post URL",
    placeholder="https://www.reddit.com/r/AskReddit/comments/abc123/...",
)

max_comments = st.slider(
    "Max comments to export",
    min_value=10,
    max_value=500,
    value=75,
    step=5,
    help="Comments are sorted by upvotes descending. Recommended: 50–100 for a 10–20 min script.",
)

scrape = st.button("🚀 Scrape post", use_container_width=True, type="primary")

st.divider()

if scrape:
    if not url.strip():
        st.warning("Please paste a Reddit URL above.")
        st.stop()

    with st.spinner("Fetching from Reddit..."):
        try:
            data = fetch_reddit(url)
        except requests.exceptions.HTTPError as e:
            st.error(f"Reddit returned an error: {e}. Make sure the post is public and the URL is correct.")
            st.stop()
        except Exception as e:
            st.error(f"Failed to fetch: {e}")
            st.stop()

    post = data[0]["data"]["children"][0]["data"]
    raw_comments = data[1]["data"]["children"]
    all_comments = flatten_comments(raw_comments)

    # ── Preview ──────────────────────────────────────────────────────────────
    st.success("Scraped successfully!")

    col1, col2, col3 = st.columns(3)
    col1.metric("Post upvotes", f"{post['score']:,}")
    col2.metric("Total comments", f"{post['num_comments']:,}")
    col3.metric("Comments exported", min(max_comments, len(all_comments)))

    st.markdown(f"**{post['title']}**")
    st.caption(f"r/{post['subreddit']}  ·  {fmt_ts(post['created_utc'])}")

    body_preview = post.get("selftext", "").strip()
    if body_preview and body_preview not in ("[removed]", "[deleted]"):
        with st.expander("Preview post body"):
            st.write(body_preview[:1500] + ("..." if len(body_preview) > 1500 else ""))

    top5 = sorted(all_comments, key=lambda c: c["score"], reverse=True)[:5]
    with st.expander(f"Preview top {min(5, len(top5))} comments"):
        for c in top5:
            label = "Top-level" if c["depth"] == 0 else f"Reply (depth {c['depth']})"
            st.markdown(f"**{c['score']:,} upvotes** · {label}")
            st.write(c["body"])
            st.divider()

    # ── Generate files ────────────────────────────────────────────────────────
    post_md = build_post_md(post)
    comments_md = build_comments_md(all_comments, max_comments)

    safe_title = "".join(
        c if c.isalnum() or c in "-_" else "_"
        for c in post["title"][:40]
    ).strip("_")

    st.divider()
    st.subheader("⬇️ Download your files")
    st.caption("Drop both files into Claude, ChatGPT, or any AI and ask it to write your YouTube script.")

    dl1, dl2 = st.columns(2)

    with dl1:
        st.download_button(
            label="📄 Download post.md",
            data=post_md.encode("utf-8"),
            file_name=f"{safe_title}_post.md",
            mime="text/markdown",
            use_container_width=True,
        )
        st.caption("Title, body, upvotes, source URL")

    with dl2:
        st.download_button(
            label="💬 Download comments.md",
            data=comments_md.encode("utf-8"),
            file_name=f"{safe_title}_comments.md",
            mime="text/markdown",
            use_container_width=True,
        )
        st.caption(f"Top {min(max_comments, len(all_comments))} comments by upvotes, no usernames")
