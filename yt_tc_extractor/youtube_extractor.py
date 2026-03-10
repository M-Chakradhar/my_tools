import streamlit as st
import re
import io

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="YouTube Transcript & Comments Extractor",
    page_icon="🎬",
    layout="centered",
)

# ── Load API key (Streamlit Secrets → env var → manual input fallback) ────────
def load_api_key():
    # 1. Streamlit Cloud secrets (recommended for deployment)
    try:
        return st.secrets["YOUTUBE_API_KEY"]
    except (KeyError, FileNotFoundError):
        pass
    # 2. Environment variable (good for local / Docker)
    import os
    key = os.environ.get("YOUTUBE_API_KEY", "")
    if key:
        return key
    # 3. Nothing found — caller will show the manual input field
    return None

YOUTUBE_API_KEY = load_api_key()

# ── Helpers ───────────────────────────────────────────────────────────────────
def extract_video_id(url):
    m = re.search(r"(?:v=|/v/|youtu\.be/|/embed/|/shorts/)([a-zA-Z0-9_-]{11})", url)
    return m.group(1) if m else None


def get_transcript(video_id):
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        try:
            transcript = transcript_list.find_manually_created_transcript(["en"])
        except Exception:
            try:
                transcript = transcript_list.find_generated_transcript(["en"])
            except Exception:
                transcript = next(iter(transcript_list))
        entries = transcript.fetch()
        text = " ".join(entry["text"].strip() for entry in entries)
        return text, None
    except Exception as e:
        return None, str(e)


def get_comments(video_id, api_key, max_comments=500):
    try:
        from googleapiclient.discovery import build
        youtube = build("youtube", "v3", developerKey=api_key)
        comments, next_page_token = [], None
        while len(comments) < max_comments:
            resp = youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                maxResults=min(100, max_comments - len(comments)),
                pageToken=next_page_token,
                textFormat="plainText",
            ).execute()
            for item in resp.get("items", []):
                text = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
                comments.append(text.strip())
            next_page_token = resp.get("nextPageToken")
            if not next_page_token:
                break
        return comments, None
    except Exception as e:
        return None, str(e)


# ── UI ────────────────────────────────────────────────────────────────────────
st.title("🎬 YouTube Extractor")
st.caption("Extract transcripts & comments — no usernames, no timestamps.")
st.divider()

video_url = st.text_input(
    "YouTube Video URL",
    placeholder="https://www.youtube.com/watch?v=...",
)

with st.expander("⚙️ Options"):
    fetch_transcript = st.checkbox("Extract Transcript", value=True)
    fetch_comments   = st.checkbox("Extract Comments",   value=True)
    max_comments     = st.slider("Max comments to fetch", 50, 1000, 200, step=50)

    # Only show the API key input if NOT already loaded from secrets/env
    if YOUTUBE_API_KEY:
        st.success("✅ YouTube API key loaded from server config — not required from you.")
        manual_api_key = None
    else:
        st.warning("No server-side API key configured.")
        manual_api_key = st.text_input(
            "Enter your YouTube Data API Key (for comments only)",
            type="password",
            placeholder="AIza...",
            help="Get a free key at https://console.cloud.google.com — enable YouTube Data API v3.",
        )

# Resolve which key to use
active_api_key = YOUTUBE_API_KEY or manual_api_key or ""

run = st.button("🚀 Extract", use_container_width=True, type="primary")

# ── Processing ────────────────────────────────────────────────────────────────
if run:
    if not video_url.strip():
        st.error("Please enter a YouTube URL.")
        st.stop()

    video_id = extract_video_id(video_url.strip())
    if not video_id:
        st.error("Could not parse a video ID from that URL. Please check the link.")
        st.stop()

    st.info(f"Video ID: `{video_id}`")

    # Transcript
    if fetch_transcript:
        with st.spinner("Fetching transcript..."):
            transcript_text, err = get_transcript(video_id)
        if transcript_text:
            st.success(f"Transcript — {len(transcript_text.split()):,} words")
            with st.expander("📄 Preview"):
                st.write(transcript_text[:3000] + ("…" if len(transcript_text) > 3000 else ""))
            st.download_button(
                "⬇️ Download Transcript (.txt)",
                data=io.BytesIO(transcript_text.encode()),
                file_name=f"transcript_{video_id}.txt",
                mime="text/plain",
                use_container_width=True,
            )
        else:
            st.warning(f"Could not fetch transcript: {err or 'Unknown error'}")

    # Comments
    if fetch_comments:
        if not active_api_key:
            st.warning("An API key is required to fetch comments.")
        else:
            with st.spinner(f"Fetching up to {max_comments} comments..."):
                comments, err = get_comments(video_id, active_api_key, max_comments)
            if comments is not None and len(comments) > 0:
                st.success(f"{len(comments):,} comments fetched")
                with st.expander("💬 Preview (first 20)"):
                    for i, c in enumerate(comments[:20], 1):
                        st.markdown(f"**{i}.** {c}")
                    if len(comments) > 20:
                        st.caption(f"…and {len(comments) - 20} more in the file.")
                comments_text = "\n\n".join(f"[{i}] {c}" for i, c in enumerate(comments, 1))
                st.download_button(
                    "⬇️ Download Comments (.txt)",
                    data=io.BytesIO(comments_text.encode()),
                    file_name=f"comments_{video_id}.txt",
                    mime="text/plain",
                    use_container_width=True,
                )
            elif comments is not None:
                st.info("No comments found (comments may be disabled on this video).")
            else:
                st.error(f"Failed to fetch comments: {err}")

st.divider()
st.caption("Built with youtube-transcript-api & YouTube Data API v3. No data stored.")
