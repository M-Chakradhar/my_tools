import streamlit as st
import re
import io
import os
import tempfile

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="YouTube Transcript & Comments Extractor",
    page_icon="🎬",
    layout="centered",
)

# ── Load API key ──────────────────────────────────────────────────────────────
def load_api_key():
    try:
        return st.secrets["YOUTUBE_API_KEY"]
    except (KeyError, FileNotFoundError):
        pass
    key = os.environ.get("YOUTUBE_API_KEY", "")
    return key if key else None

YOUTUBE_API_KEY = load_api_key()

# ── Helpers ───────────────────────────────────────────────────────────────────
def extract_video_id(url):
    m = re.search(r"(?:v=|/v/|youtu\.be/|/embed/|/shorts/)([a-zA-Z0-9_-]{11})", url)
    return m.group(1) if m else None


def clean_vtt(vtt_text):
    """Strip VTT formatting and return clean plain text."""
    # Remove WEBVTT header
    lines = vtt_text.splitlines()
    text_lines = []
    for line in lines:
        line = line.strip()
        # Skip headers, timestamps, blank lines, cue numbers
        if not line:
            continue
        if line.startswith("WEBVTT") or line.startswith("Kind:") or line.startswith("Language:"):
            continue
        if re.match(r"^\d{2}:\d{2}", line) or re.match(r"^\d+$", line):
            continue
        # Remove HTML tags like <00:00:01.000><c> etc.
        line = re.sub(r"<[^>]+>", "", line)
        if line:
            text_lines.append(line)

    # Deduplicate consecutive identical lines (common in auto-captions)
    deduped = []
    for line in text_lines:
        if not deduped or line != deduped[-1]:
            deduped.append(line)

    return " ".join(deduped)


def get_transcript(video_id):
    try:
        import yt_dlp

        with tempfile.TemporaryDirectory() as tmpdir:
            ydl_opts = {
                "skip_download": True,
                "writeautomaticsub": True,
                "writesubtitles": True,
                "subtitleslangs": ["en", "en-US", "en-GB"],
                "subtitlesformat": "vtt",
                "outtmpl": os.path.join(tmpdir, "%(id)s.%(ext)s"),
                "quiet": True,
                "no_warnings": True,
            }

            url = f"https://www.youtube.com/watch?v={video_id}"

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            # Find the downloaded .vtt file
            vtt_file = None
            for fname in os.listdir(tmpdir):
                if fname.endswith(".vtt"):
                    vtt_file = os.path.join(tmpdir, fname)
                    break

            if not vtt_file:
                return None, "No captions/subtitles found for this video."

            with open(vtt_file, "r", encoding="utf-8") as f:
                vtt_text = f.read()

            transcript = clean_vtt(vtt_text)
            if not transcript.strip():
                return None, "Captions file was empty after processing."

            return transcript, None

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

    if YOUTUBE_API_KEY:
        st.success("✅ YouTube API key loaded from server config.")
        manual_api_key = None
    else:
        st.warning("No server-side API key configured.")
        manual_api_key = st.text_input(
            "Enter your YouTube Data API Key (for comments only)",
            type="password",
            placeholder="AIza...",
        )

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

    if fetch_transcript:
        with st.spinner("Fetching transcript... (this may take 20–30 seconds)"):
            transcript_text, err = get_transcript(video_id)
        if transcript_text:
            st.success(f"✅ Transcript — {len(transcript_text.split()):,} words")
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

    if fetch_comments:
        if not active_api_key:
            st.warning("An API key is required to fetch comments.")
        else:
            with st.spinner(f"Fetching up to {max_comments} comments..."):
                comments, err = get_comments(video_id, active_api_key, max_comments)
            if comments is not None and len(comments) > 0:
                st.success(f"✅ {len(comments):,} comments fetched")
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
st.caption("Built with yt-dlp & YouTube Data API v3. No data stored.")
