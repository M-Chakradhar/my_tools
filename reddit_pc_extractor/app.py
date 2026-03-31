import streamlit as st
import praw
import re
from datetime import datetime, timezone

@st.cache_resource
def get_reddit():
    return praw.Reddit(
        client_id=st.secrets["REDDIT_CLIENT_ID"],
        client_secret=st.secrets["REDDIT_CLIENT_SECRET"],
        user_agent="RedditScriptScraper/1.0 (by personal use)",
    )

def fmt_ts(unix: float) -> str:
    return datetime.fromtimestamp(unix, tz=timezone.utc).strftime("%Y-%m-%d")

def extract_post_id(url: str) -> str:
    match = re.search(r"/comments/([a-z0-9]+)", url, re.IGNORECASE)
    if not match:
        raise ValueError("Could not find a post ID in that URL.")
    return match.group(1)

def flatten_comments(comment_forest, depth: int = 0) -> list:
    results = []
    for item in comment_forest:
        if isinstance(item, praw.models.MoreComments):
            continue
        body = item.body.strip() if hasattr(item, "body") else ""
        if body in ("[deleted]", "[removed]", ""):
            continue
        results.append({
            "depth": depth,
            "score": item.score,
            "body": body,
            "created": fmt_ts(item.created_utc),
        })
        if item.replies:
            results.extend(flatten_comments(item.replies, depth + 1))
    return results

def build_post_md(submission) -> str:
    lines = [
        f"# {submission.title}",
        "",
        f"**Subreddit:** r/{submission.subreddit.display_name}",
        f"**Upvotes:** {submission.score:,}  |  **Upvote ratio:** {int(submission.upvote_ratio * 100)}%",
        f"**Total comments:** {submission.num_comments:,}",
        f"**Posted:** {fmt_ts(submission.created_utc)}",
        f"**Source:** https://reddit.com{submission.permalink}",
        "",
        "---",
        "",
    ]
    body = (submission.selftext or "").strip()
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
        level = "Top-level" if c["depth"] == 0 else f"Reply (depth {c['depth']})"
        lines += [
            f"## Comment {i}  ·  {c['score']:,} upvotes  ·  {level}",
            "",
            c["body"],
            "",
            "---",
            "",
        ]
    return "\n".join(lines)

# ── UI ────────────────────────────────────────────────────────────────────────

st.set_page_config(page_title="Reddit → Script Scraper", page_icon="🎬", layout="centered")

st.title("🎬 Reddit → Script Scraper")
st.caption("Paste a Reddit post URL. Get two clean .md files ready to drop into any AI for a YouTube script.")

st.divider()

url = st.text_input("Reddit post URL", placeholder="https://www.reddit.com/r/AskReddit/comments/abc123/...")

max_comments = st.slider(
    "Max comments to export", min_value=10, max_value=500, value=75, step=5,
    help="Sorted by upvotes descending. Recommended: 50–100 for a 10–20 min script.",
)

scrape = st.button("🚀 Scrape post", use_container_width=True, type="primary")

st.divider()

if scrape:
    if not url.strip():
        st.warning("Please paste a Reddit URL above.")
        st.stop()

    with st.spinner("Connecting to Reddit API..."):
        try:
            reddit = get_reddit()
            post_id = extract_post_id(url)
            submission = reddit.submission(id=post_id)
            submission.comments.replace_more(limit=None)
            all_comments = flatten_comments(submission.comments)
        except ValueError as e:
            st.error(str(e))
            st.stop()
        except Exception as e:
            st.error(f"Failed to fetch: {e}")
            st.stop()

    st.success("Scraped successfully!")

    col1, col2, col3 = st.columns(3)
    col1.metric("Post upvotes", f"{submission.score:,}")
    col2.metric("Total comments", f"{submission.num_comments:,}")
    col3.metric("Comments exported", min(max_comments, len(all_comments)))

    st.markdown(f"**{submission.title}**")
    st.caption(f"r/{submission.subreddit.display_name}  ·  {fmt_ts(submission.created_utc)}")

    body_preview = (submission.selftext or "").strip()
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

    post_md = build_post_md(submission)
    comments_md = build_comments_md(all_comments, max_comments)

    safe_title = "".join(
        c if c.isalnum() or c in "-_" else "_"
        for c in submission.title[:40]
    ).strip("_")

    st.divider()
    st.subheader("⬇️ Download your files")
    st.caption("Drop both into Claude, ChatGPT, or any AI and ask it to write your YouTube script.")

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
