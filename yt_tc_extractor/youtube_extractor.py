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
    lines = vtt_text.splitlines()
    text_lines = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("WEBVTT") or line.startswith("Kind:") or line.startswith("Language:"):
            continue
        if re.match(r"^\d{2}:\d{2}", line) or re.match(r"^\d+$", line):
            continue
        line = re.sub(r"<[^>]+>", "", line)
        if line:
            text_lines.append(line)
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
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([f"https://www.youtube.com/watch?v={video_id}"])
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


def get_total_comment_count(video_id, api_key):
    try:
        from googleapiclient.discovery import build
        youtube = build("youtube", "v3", developerKey=api_key)
        resp = youtube.videos().list(part="statistics", id=video_id).execute()
        items = resp.get("items", [])
        if not items:
            return None
        count = items[0]["statistics"].get("commentCount")
        return int(count) if count else None
    except Exception:
        return None


def get_comments(video_id, api_key, max_comments=500, progress_bar=None):
    """Fetch top-level comments AND their replies, up to max_comments total."""
    try:
        from googleapiclient.discovery import build
        youtube = build("youtube", "v3", developerKey=api_key)

        all_comments = []
        next_page_token = None

        while len(all_comments) < max_comments:
            # Fetch a page of top-level comment threads
            resp = youtube.commentThreads().list(
                part="snippet,replies",
                videoId=video_id,
                maxResults=min(100, max_comments - len(all_comments)),
                pageToken=next_page_token,
                textFormat="plainText",
            ).execute()

            for item in resp.get("items", []):
                if len(all_comments) >= max_comments:
                    break

                # Add top-level comment
                top = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"].strip()
                all_comments.append(top)

                reply_count = item["snippet"].get("totalReplyCount", 0)
                if reply_count == 0 or len(all_comments) >= max_comments:
                    continue

                # Replies already embedded in response (up to 5)
                embedded_replies = item.get("replies", {}).get("comments", [])

                if len(embedded_replies) >= reply_count:
                    # All replies already included in the thread response
                    for reply in embedded_replies:
                        if len(all_comments) >= max_comments:
                            break
                        text = reply["snippet"]["textDisplay"].strip()
                        all_comments.append(f"  ↳ {text}")
                else:
                    # More replies exist — fetch them via comments.list
                    thread_id = item["id"]
                    reply_page_token = None
                    while len(all_comments) < max_comments:
                        reply_resp = youtube.comments().list(
                            part="snippet",
                            parentId=thread_id,
                            maxResults=min(100, max_comments - len(all_comments)),
                            pageToken=reply_page_token,
                            textFormat="plainText",
                        ).execute()
                        for r in reply_resp.get("items", []):
                            if len(all_comments) >= max_comments:
                                break
                            text = r["snippet"]["textDisplay"].strip()
                            all_comments.append(f"  ↳ {text}")
                        reply_page_token = reply_resp.get("nextPageToken")
                        if not reply_page_token:
                            break

                if progress_bar:
                    progress_bar.progress(min(len(all_comments) / max_comments, 1.0))

            next_page_token = resp.get("nextPageToken")
            if not next_page_token:
                break

        return all_comments, None
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

# Show total comment count as soon as URL is entered
if video_url.strip():
    video_id_preview = extract_video_id(video_url.strip())
    if video_id_preview and YOUTUBE_API_KEY:
        total = get_total_comment_count(video_id_preview, YOUTUBE_API_KEY)
        if total is not None:
            st.info(f"💬 This video has **{total:,} total comments** (including replies) on YouTube. Use this to decide how many to download below.")

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

    # ── Transcript ────────────────────────────────────────────────────────────
    if fetch_transcript:
        with st.spinner("Fetching transcript... (this may take 20–30 seconds)"):
            transcript_text, err = get_transcript(video_id)
        if transcript_text:
            word_count = len(transcript_text.split())
            char_count = len(transcript_text)
            col1, col2 = st.columns(2)
            col1.metric("📝 Word Count", f"{word_count:,}")
            col2.metric("🔤 Characters", f"{char_count:,}")
            st.success("✅ Transcript ready")
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

    # ── Comments ──────────────────────────────────────────────────────────────
    if fetch_comments:
        if not active_api_key:
            st.warning("An API key is required to fetch comments.")
        else:
            total = get_total_comment_count(video_id, active_api_key)
            if total is not None:
                st.caption(f"ℹ️ Fetching {max_comments:,} of {total:,} total comments (including replies).")

            progress_bar = st.progress(0, text="Fetching comments and replies...")
            comments, err = get_comments(video_id, active_api_key, max_comments, progress_bar)
            progress_bar.empty()

            if comments is not None and len(comments) > 0:
                top_level = sum(1 for c in comments if not c.startswith("  ↳"))
                replies    = sum(1 for c in comments if c.startswith("  ↳"))

                col1, col2, col3 = st.columns(3)
                col1.metric("💬 Total Fetched", f"{len(comments):,}")
                col2.metric("🗨️ Top-level", f"{top_level:,}")
                col3.metric("↳ Replies", f"{replies:,}")
                if total:
                    st.caption(f"📊 Video has {total:,} total comments on YouTube.")

                st.success("✅ Comments ready")
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
