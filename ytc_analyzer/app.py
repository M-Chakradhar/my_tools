import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import isodate
from datetime import datetime, timezone
from collections import Counter
import re
import time

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="YT Channel Intelligence",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS — dark, editorial, data-dense ──────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap');

:root {
    --bg:       #0a0a0f;
    --surface:  #13131a;
    --border:   #1e1e2e;
    --accent:   #e63946;
    --accent2:  #f4a261;
    --text:     #e8e8f0;
    --muted:    #6b6b7b;
    --green:    #2ec4b6;
    --mono:     'Space Mono', monospace;
    --sans:     'DM Sans', sans-serif;
}

html, body, [data-testid="stAppViewContainer"] {
    background: var(--bg) !important;
    color: var(--text);
    font-family: var(--sans);
}

[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border);
}

[data-testid="stSidebar"] * { color: var(--text) !important; }

h1, h2, h3 { font-family: var(--mono); letter-spacing: -0.02em; }

/* Stat cards */
.stat-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 24px; }
.stat-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 20px 24px;
    position: relative;
    overflow: hidden;
}
.stat-card::before {
    content: '';
    position: absolute; top: 0; left: 0;
    width: 3px; height: 100%;
    background: var(--accent);
}
.stat-card.green::before { background: var(--green); }
.stat-card.orange::before { background: var(--accent2); }
.stat-label { font-size: 11px; font-family: var(--mono); color: var(--muted); letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 8px; }
.stat-value { font-size: 28px; font-family: var(--mono); font-weight: 700; color: var(--text); line-height: 1; }
.stat-sub { font-size: 12px; color: var(--muted); margin-top: 6px; }

/* Section headers */
.section-header {
    display: flex; align-items: center; gap: 10px;
    border-bottom: 1px solid var(--border);
    padding-bottom: 10px; margin: 32px 0 20px;
}
.section-header h2 { font-size: 14px; font-family: var(--mono); color: var(--muted); letter-spacing: 0.1em; text-transform: uppercase; margin: 0; }
.section-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--accent); flex-shrink: 0; }

/* Channel banner */
.channel-banner {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 28px 32px;
    display: flex; align-items: center; gap: 24px;
    margin-bottom: 28px;
}
.channel-avatar { width: 80px; height: 80px; border-radius: 50%; border: 2px solid var(--accent); object-fit: cover; }
.channel-name { font-size: 26px; font-family: var(--mono); font-weight: 700; }
.channel-handle { font-size: 13px; color: var(--muted); font-family: var(--mono); margin-top: 4px; }
.channel-desc { font-size: 13px; color: var(--muted); margin-top: 8px; line-height: 1.6; max-width: 700px; }
.channel-country { font-size: 11px; font-family: var(--mono); color: var(--accent2); margin-top: 6px; letter-spacing: 0.05em; }

/* Tab styling */
[data-baseweb="tab-list"] { background: var(--surface) !important; border-radius: 8px; padding: 4px; gap: 4px; border: 1px solid var(--border); }
[data-baseweb="tab"] { background: transparent !important; color: var(--muted) !important; font-family: var(--mono) !important; font-size: 12px !important; border-radius: 6px !important; }
[aria-selected="true"][data-baseweb="tab"] { background: var(--accent) !important; color: white !important; }

/* Input fields */
[data-testid="stTextInput"] input {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
    font-family: var(--mono) !important;
    border-radius: 6px !important;
}

[data-testid="stSelectbox"] > div > div {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
}

/* Button */
[data-testid="stButton"] button {
    background: var(--accent) !important;
    color: white !important;
    border: none !important;
    font-family: var(--mono) !important;
    font-weight: 700 !important;
    letter-spacing: 0.05em !important;
    border-radius: 6px !important;
    padding: 10px 28px !important;
    transition: opacity 0.2s !important;
}
[data-testid="stButton"] button:hover { opacity: 0.85 !important; }

/* Dataframe */
[data-testid="stDataFrame"] { border: 1px solid var(--border) !important; border-radius: 8px; }

/* Spinner */
[data-testid="stSpinner"] { color: var(--accent) !important; }

/* Plotly chart background */
.js-plotly-plot .plotly { background: transparent !important; }

.stAlert { border-radius: 8px !important; }

/* Metric delta */
[data-testid="stMetricDelta"] { font-family: var(--mono) !important; }

div[data-testid="metric-container"] {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 16px;
}
</style>
""", unsafe_allow_html=True)

# ── Plotly dark template ──────────────────────────────────────────────────────
PLOTLY_THEME = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Space Mono, monospace", color="#e8e8f0", size=11),
    xaxis=dict(gridcolor="#1e1e2e", linecolor="#1e1e2e", showgrid=True),
    yaxis=dict(gridcolor="#1e1e2e", linecolor="#1e1e2e", showgrid=True),
    margin=dict(l=40, r=20, t=40, b=40),
)

ACCENT   = "#e63946"
ACCENT2  = "#f4a261"
GREEN    = "#2ec4b6"
MUTED    = "#6b6b7b"
PURPLE   = "#9b72cf"

# ── Helpers ───────────────────────────────────────────────────────────────────
def fmt_number(n):
    if n is None: return "N/A"
    n = int(n)
    if n >= 1_000_000_000: return f"{n/1_000_000_000:.2f}B"
    if n >= 1_000_000:     return f"{n/1_000_000:.2f}M"
    if n >= 1_000:         return f"{n/1_000:.1f}K"
    return str(n)

def parse_duration(iso):
    try:
        secs = int(isodate.parse_duration(iso).total_seconds())
        return secs
    except:
        return 0

def is_short(duration_sec, title=""):
    return duration_sec <= 60 or "#shorts" in title.lower() or "#short" in title.lower()

def engagement_rate(views, likes, comments):
    if not views or views == 0: return 0
    return round(((likes or 0) + (comments or 0)) / views * 100, 3)

# ── API functions ─────────────────────────────────────────────────────────────
API_BASE = "https://www.googleapis.com/youtube/v3"

def get_api_key():
    try:
        return st.secrets["YOUTUBE_API_KEY"]
    except:
        return None

def resolve_channel(identifier: str, api_key: str):
    """Accept URL, handle (@name), or channel ID."""
    identifier = identifier.strip()

    # Extract from URL
    patterns = [
        r"youtube\.com/channel/([UC][a-zA-Z0-9_-]{22})",
        r"youtube\.com/@([\w.-]+)",
        r"youtube\.com/c/([\w.-]+)",
        r"youtube\.com/user/([\w.-]+)",
    ]
    channel_id, handle = None, None
    for p in patterns:
        m = re.search(p, identifier)
        if m:
            val = m.group(1)
            if val.startswith("UC") and len(val) == 24:
                channel_id = val
            else:
                handle = val
            break

    if not channel_id and not handle:
        # Raw input
        if identifier.startswith("UC") and len(identifier) == 24:
            channel_id = identifier
        elif identifier.startswith("@"):
            handle = identifier[1:]
        else:
            handle = identifier

    if channel_id:
        return fetch_channel_by_id(channel_id, api_key)
    else:
        return fetch_channel_by_handle(handle, api_key)

def fetch_channel_by_id(channel_id, api_key):
    r = requests.get(f"{API_BASE}/channels", params={
        "part": "snippet,statistics,brandingSettings",
        "id": channel_id, "key": api_key
    })
    data = r.json()
    if "error" in data:
        return None, data["error"].get("message", "API Error")
    items = data.get("items", [])
    if not items:
        return None, "Channel not found."
    return items[0], None

def fetch_channel_by_handle(handle, api_key):
    r = requests.get(f"{API_BASE}/channels", params={
        "part": "snippet,statistics,brandingSettings",
        "forHandle": handle, "key": api_key
    })
    data = r.json()
    if "error" in data:
        return None, data["error"].get("message", "API Error")
    items = data.get("items", [])
    if not items:
        # fallback to search
        r2 = requests.get(f"{API_BASE}/search", params={
            "part": "snippet", "type": "channel",
            "q": handle, "maxResults": 1, "key": api_key
        })
        d2 = r2.json()
        if "error" in d2:
            return None, d2["error"].get("message", "API Error")
        items2 = d2.get("items", [])
        if not items2:
            return None, "Channel not found."
        cid = items2[0]["snippet"]["channelId"]
        return fetch_channel_by_id(cid, api_key)
    return items[0], None

def get_uploads_playlist_id(channel_id, api_key):
    r = requests.get(f"{API_BASE}/channels", params={
        "part": "contentDetails", "id": channel_id, "key": api_key
    })
    data = r.json()
    try:
        return data["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"], None
    except:
        return None, "Could not find uploads playlist."

def fetch_video_ids(playlist_id, api_key, limit=None):
    ids, token = [], None
    fetched = 0
    while True:
        params = {"part": "contentDetails", "playlistId": playlist_id,
                  "maxResults": 50, "key": api_key}
        if token:
            params["pageToken"] = token
        r = requests.get(f"{API_BASE}/playlistItems", params=params)
        data = r.json()
        if "error" in data:
            return ids, data["error"].get("message", "API Error")
        batch = [i["contentDetails"]["videoId"] for i in data.get("items", [])]
        ids.extend(batch)
        fetched += len(batch)
        token = data.get("nextPageToken")
        if not token:
            break
        if limit and fetched >= limit:
            break
    return ids[:limit] if limit else ids, None

def fetch_video_details(video_ids, api_key, progress_bar=None):
    details = []
    total = len(video_ids)
    for i in range(0, total, 50):
        chunk = video_ids[i:i+50]
        r = requests.get(f"{API_BASE}/videos", params={
            "part": "snippet,statistics,contentDetails",
            "id": ",".join(chunk), "key": api_key
        })
        data = r.json()
        if "error" in data:
            return details, data["error"].get("message", "API Error")
        for item in data.get("items", []):
            snip  = item.get("snippet", {})
            stats = item.get("statistics", {})
            cd    = item.get("contentDetails", {})
            dur   = parse_duration(cd.get("duration", "PT0S"))
            title = snip.get("title", "")
            pub   = snip.get("publishedAt", "")
            dt    = datetime.fromisoformat(pub.replace("Z", "+00:00")) if pub else None
            details.append({
                "video_id":       item["id"],
                "title":          title,
                "published_at":   dt,
                "year":           dt.year if dt else None,
                "month":          dt.strftime("%Y-%m") if dt else None,
                "day_of_week":    dt.strftime("%A") if dt else None,
                "hour":           dt.hour if dt else None,
                "duration_sec":   dur,
                "duration_min":   round(dur / 60, 2),
                "is_short":       is_short(dur, title),
                "views":          int(stats.get("viewCount", 0)),
                "likes":          int(stats.get("likeCount", 0)),
                "comments":       int(stats.get("commentCount", 0)),
                "tags":           snip.get("tags", []),
                "category_id":    snip.get("categoryId", ""),
                "thumbnail":      snip.get("thumbnails", {}).get("medium", {}).get("url", ""),
                "description":    snip.get("description", "")[:300],
            })
        if progress_bar:
            progress_bar.progress(min((i + 50) / total, 1.0))
        time.sleep(0.05)
    return details, None

# ── Chart builders ────────────────────────────────────────────────────────────

def chart_shorts_vs_long(df):
    counts = df["is_short"].value_counts().reset_index()
    counts.columns = ["type", "count"]
    counts["type"] = counts["type"].map({True: "Shorts", False: "Long Videos"})
    fig = px.pie(counts, names="type", values="count",
                 color="type", color_discrete_map={"Shorts": ACCENT, "Long Videos": GREEN},
                 hole=0.55)
    fig.update_traces(textfont_family="Space Mono")
    fig.update_layout(**PLOTLY_THEME, title="Shorts vs Long Videos", height=340,
                      legend=dict(orientation="h", y=-0.1))
    return fig

def chart_videos_over_time(df):
    monthly = df.groupby("month").size().reset_index(name="videos")
    monthly = monthly.sort_values("month")
    fig = px.bar(monthly, x="month", y="videos",
                 color_discrete_sequence=[ACCENT])
    fig.update_layout(**PLOTLY_THEME, title="Videos Posted Per Month", height=340,
                      xaxis_title="Month", yaxis_title="# Videos")
    return fig

def chart_cumulative_videos(df):
    sorted_df = df.sort_values("published_at")
    sorted_df["cumulative"] = range(1, len(sorted_df)+1)
    fig = px.area(sorted_df, x="published_at", y="cumulative",
                  color_discrete_sequence=[ACCENT])
    fig.update_traces(line_width=2, fillcolor=f"rgba(230,57,70,0.15)")
    fig.update_layout(**PLOTLY_THEME, title="Cumulative Videos Over Time", height=340,
                      xaxis_title="Date", yaxis_title="Total Videos")
    return fig

def chart_posting_heatmap(df):
    days_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    heat = df.groupby(["day_of_week","hour"]).size().reset_index(name="count")
    pivot = heat.pivot(index="day_of_week", columns="hour", values="count").fillna(0)
    pivot = pivot.reindex([d for d in days_order if d in pivot.index])
    fig = go.Figure(go.Heatmap(
        z=pivot.values, x=[f"{h:02d}:00" for h in pivot.columns],
        y=pivot.index.tolist(),
        colorscale=[[0,"#13131a"],[0.5,f"rgba(230,57,70,0.6)"],[1,ACCENT]],
        showscale=True
    ))
    fig.update_layout(**PLOTLY_THEME, title="Posting Heatmap — Day × Hour (UTC)",
                      height=340, xaxis_title="Hour (UTC)", yaxis_title="")
    return fig

def chart_views_scatter(df, subs):
    df2 = df.copy()
    df2["vps"] = df2["views"] / max(subs, 1)
    df2["type"] = df2["is_short"].map({True: "Short", False: "Long"})
    df2["label"] = df2["title"].str[:40]
    fig = px.scatter(df2.sort_values("published_at"), x="published_at", y="views",
                     color="type", size="vps", hover_name="label",
                     color_discrete_map={"Short": ACCENT, "Long": GREEN},
                     size_max=30, opacity=0.8)
    fig.update_layout(**PLOTLY_THEME, title="Views per Video Over Time (bubble = views/subscriber)",
                      height=420, xaxis_title="Published", yaxis_title="Views")
    return fig

def chart_avg_views_by_year(df):
    yr = df.groupby("year")["views"].mean().reset_index()
    yr.columns = ["year", "avg_views"]
    yr = yr.dropna()
    fig = px.bar(yr, x="year", y="avg_views", color_discrete_sequence=[ACCENT2])
    fig.update_layout(**PLOTLY_THEME, title="Average Views by Year", height=340,
                      xaxis_title="Year", yaxis_title="Avg Views")
    return fig

def chart_top_videos(df, subs, n=20):
    df2 = df.copy()
    df2["vps"] = df2["views"] / max(subs, 1)
    top = df2.nlargest(n, "vps")[["title","views","likes","comments","vps","is_short","published_at"]]
    top["title_short"] = top["title"].str[:45]
    top["type"] = top["is_short"].map({True:"Short","False":"Long",False:"Long"})
    fig = px.bar(top.sort_values("vps"), x="vps", y="title_short", orientation="h",
                 color="type", color_discrete_map={"Short": ACCENT, "Long": GREEN},
                 hover_data={"views": True, "likes": True, "comments": True,
                             "published_at": True, "vps": ":.3f"})
    fig.update_layout(**PLOTLY_THEME, title=f"Top {n} Videos — Views per Subscriber",
                      height=max(400, n*28), yaxis_title="", xaxis_title="Views / Subscriber",
                      yaxis=dict(tickfont=dict(size=10)))
    return fig

def chart_engagement_trend(df):
    df2 = df.copy()
    df2["eng_rate"] = df2.apply(lambda r: engagement_rate(r.views, r.likes, r.comments), axis=1)
    df2 = df2.sort_values("published_at")
    df2["rolling_eng"] = df2["eng_rate"].rolling(10, min_periods=1).mean()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df2["published_at"], y=df2["eng_rate"],
                             mode="markers", marker=dict(color=MUTED, size=4), name="Per Video",
                             opacity=0.5))
    fig.add_trace(go.Scatter(x=df2["published_at"], y=df2["rolling_eng"],
                             mode="lines", line=dict(color=ACCENT, width=2.5), name="Rolling Avg (10)"))
    fig.update_layout(**PLOTLY_THEME, title="Engagement Rate Over Time (%)", height=360,
                      xaxis_title="Published", yaxis_title="Engagement Rate %")
    return fig

def chart_likes_comments_trend(df):
    df2 = df.sort_values("published_at").copy()
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        subplot_titles=("Likes per Video", "Comments per Video"),
                        vertical_spacing=0.08)
    fig.add_trace(go.Scatter(x=df2["published_at"], y=df2["likes"].rolling(10,min_periods=1).mean(),
                             line=dict(color=ACCENT2, width=2), name="Likes (rolling avg)"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df2["published_at"], y=df2["comments"].rolling(10,min_periods=1).mean(),
                             line=dict(color=GREEN, width=2), name="Comments (rolling avg)"), row=2, col=1)
    fig.update_layout(**PLOTLY_THEME, title="Likes & Comments Trend", height=440, showlegend=True)
    return fig

def chart_duration_histogram(df):
    long_df = df[~df["is_short"]].copy()
    long_df["duration_min_clip"] = long_df["duration_min"].clip(upper=120)
    fig = px.histogram(long_df, x="duration_min_clip", nbins=40,
                       color_discrete_sequence=[ACCENT])
    fig.update_layout(**PLOTLY_THEME, title="Long Video Duration Distribution (min)",
                      height=340, xaxis_title="Duration (minutes)", yaxis_title="Count")
    return fig

def chart_shorts_vs_long_performance(df):
    grp = df.groupby("is_short").agg(
        avg_views=("views","mean"),
        avg_likes=("likes","mean"),
        avg_comments=("comments","mean")
    ).reset_index()
    grp["type"] = grp["is_short"].map({True:"Shorts", False:"Long Videos"})
    fig = px.bar(grp.melt(id_vars="type", value_vars=["avg_views","avg_likes","avg_comments"]),
                 x="variable", y="value", color="type", barmode="group",
                 color_discrete_map={"Shorts": ACCENT, "Long Videos": GREEN},
                 labels={"variable":"Metric","value":"Average","type":"Type"})
    fig.update_layout(**PLOTLY_THEME, title="Shorts vs Long — Avg Performance", height=340)
    return fig

def chart_views_per_year_type(df):
    grp = df.groupby(["year","is_short"])["views"].mean().reset_index()
    grp["type"] = grp["is_short"].map({True:"Shorts", False:"Long"})
    grp = grp.dropna(subset=["year"])
    grp["year"] = grp["year"].astype(int).astype(str)
    fig = px.bar(grp, x="year", y="views", color="type", barmode="group",
                 color_discrete_map={"Shorts": ACCENT, "Long": GREEN})
    fig.update_layout(**PLOTLY_THEME, title="Avg Views by Year & Type", height=340,
                      xaxis_title="Year", yaxis_title="Avg Views")
    return fig

def chart_title_wordcloud_bar(df, n=20, top_only=True):
    if top_only:
        threshold = df["views"].quantile(0.75)
        source = df[df["views"] >= threshold]["title"]
    else:
        source = df["title"]
    stopwords = {"the","a","an","in","of","to","and","is","for","on","with","my","your",
                 "this","that","how","i","you","we","it","its","our","are","was","be",
                 "at","by","from","as","up","or","if","so","do","not","but","what",
                 "he","she","they","all","more","new","get","can","will","one","have"}
    words = []
    for title in source:
        tokens = re.findall(r"[a-zA-Z]{3,}", title.lower())
        words.extend([w for w in tokens if w not in stopwords])
    freq = Counter(words).most_common(n)
    if not freq:
        return None
    words_list, counts = zip(*freq)
    fig = px.bar(x=list(counts), y=list(words_list), orientation="h",
                 color=list(counts), color_continuous_scale=[[0,MUTED],[0.5,ACCENT2],[1,ACCENT]])
    fig.update_layout(**PLOTLY_THEME, title=f"Top {n} Words in {'Top 25%' if top_only else 'All'} Titles",
                      height=max(380, n*26), yaxis_title="", xaxis_title="Frequency",
                      coloraxis_showscale=False,
                      yaxis=dict(tickfont=dict(size=11), categoryorder="total ascending"))
    return fig

def chart_top_titles_by_vps(df, subs, n=25):
    df2 = df[~df["is_short"]].copy()
    df2["vps"] = df2["views"] / max(subs, 1)
    top = df2.nlargest(n, "vps")[["title","vps","views","published_at"]].copy()
    top["label"] = top["title"].str[:50]
    fig = px.bar(top.sort_values("vps"), x="vps", y="label", orientation="h",
                 color="vps", color_continuous_scale=[[0,MUTED],[0.5,ACCENT2],[1,ACCENT]],
                 hover_data={"views": True, "published_at": True})
    fig.update_layout(**PLOTLY_THEME,
                      title=f"Top {n} Long Video Titles — Views per Subscriber",
                      height=max(420, n*26), yaxis_title="", xaxis_title="Views / Subscriber",
                      coloraxis_showscale=False,
                      yaxis=dict(tickfont=dict(size=10), categoryorder="total ascending"))
    return fig

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='padding: 4px 0 20px;'>
        <div style='font-family: Space Mono; font-size: 18px; font-weight: 700; color: #e63946;'>📡 YT Intelligence</div>
        <div style='font-size: 11px; color: #6b6b7b; font-family: Space Mono; margin-top: 4px;'>Channel Analyzer v1.0</div>
    </div>
    """, unsafe_allow_html=True)

    channel_input = st.text_input(
        "YouTube Channel URL or Handle",
        placeholder="@mkbhd  /  youtube.com/c/...",
    )

    st.markdown("---")
    st.markdown("<div style='font-size:11px; font-family: Space Mono; color:#6b6b7b; text-transform:uppercase; letter-spacing:0.08em;'>Fetch Limit</div>", unsafe_allow_html=True)

    limit_mode = st.radio("", ["All Videos", "Fixed Options", "Custom Number"],
                          label_visibility="collapsed")

    video_limit = None
    if limit_mode == "Fixed Options":
        video_limit = st.selectbox("Select limit", [500, 1000, 1500, 2000])
    elif limit_mode == "Custom Number":
        video_limit = st.number_input("Custom limit", min_value=50, max_value=10000,
                                      value=500, step=50)

    st.markdown("")
    analyze_btn = st.button("▶  ANALYZE CHANNEL", use_container_width=True)

    st.markdown("---")
    st.markdown("""
    <div style='font-size:10px; color:#6b6b7b; font-family: Space Mono; line-height:1.8;'>
    ⚠️ YouTube API quota:<br>
    ~10,000 units/day (free tier)<br><br>
    💡 Large channels may use<br>significant quota. Use a limit<br>for 1000+ video channels.
    </div>
    """, unsafe_allow_html=True)

# ── Main area ─────────────────────────────────────────────────────────────────
api_key = get_api_key()

if not api_key:
    st.markdown("""
    <div style='text-align:center; padding: 80px 20px;'>
        <div style='font-family: Space Mono; font-size: 32px; font-weight: 700; color: #e63946;'>📡</div>
        <div style='font-family: Space Mono; font-size: 22px; font-weight: 700; margin: 16px 0 8px;'>YT Channel Intelligence</div>
        <div style='color: #6b6b7b; font-size: 14px; max-width: 420px; margin: 0 auto; line-height: 1.7;'>
            No API key found. Add <code>YOUTUBE_API_KEY</code> to your Streamlit secrets to get started.
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

if not analyze_btn:
    st.markdown("""
    <div style='text-align:center; padding: 100px 20px;'>
        <div style='font-family: Space Mono; font-size: 48px;'>📡</div>
        <div style='font-family: Space Mono; font-size: 26px; font-weight: 700; margin: 20px 0 10px;'>YT Channel Intelligence</div>
        <div style='color: #6b6b7b; font-size: 15px; max-width: 480px; margin: 0 auto; line-height: 1.8;'>
            Paste a YouTube channel URL or handle in the sidebar.<br>
            Understand what makes any creator tick.
        </div>
        <div style='margin-top: 40px; display: flex; gap: 20px; justify-content: center; flex-wrap: wrap;'>
            <div style='background:#13131a; border:1px solid #1e1e2e; border-radius:8px; padding:16px 24px; font-family:Space Mono; font-size:12px; color:#6b6b7b;'>📊 Posting patterns</div>
            <div style='background:#13131a; border:1px solid #1e1e2e; border-radius:8px; padding:16px 24px; font-family:Space Mono; font-size:12px; color:#6b6b7b;'>🏆 Top performing videos</div>
            <div style='background:#13131a; border:1px solid #1e1e2e; border-radius:8px; padding:16px 24px; font-family:Space Mono; font-size:12px; color:#6b6b7b;'>💬 Engagement trends</div>
            <div style='background:#13131a; border:1px solid #1e1e2e; border-radius:8px; padding:16px 24px; font-family:Space Mono; font-size:12px; color:#6b6b7b;'>🔤 Title intelligence</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

if not channel_input.strip():
    st.error("Please enter a YouTube channel URL or handle in the sidebar.")
    st.stop()

# ── Fetch data ────────────────────────────────────────────────────────────────
with st.spinner("Resolving channel..."):
    channel_data, err = resolve_channel(channel_input, api_key)

if err:
    st.error(f"Error: {err}")
    st.stop()

snippet  = channel_data.get("snippet", {})
stats    = channel_data.get("statistics", {})
channel_id = channel_data["id"]
channel_name = snippet.get("title", "Unknown")
handle   = snippet.get("customUrl", "")
desc     = snippet.get("description", "")[:280]
country  = snippet.get("country", "")
avatar   = snippet.get("thumbnails", {}).get("medium", {}).get("url", "")
created  = snippet.get("publishedAt", "")
subs     = int(stats.get("subscriberCount", 0))
total_views = int(stats.get("viewCount", 0))
total_vids  = int(stats.get("videoCount", 0))

created_dt = datetime.fromisoformat(created.replace("Z","+00:00")) if created else None
channel_age_years = round((datetime.now(timezone.utc) - created_dt).days / 365.25, 1) if created_dt else None

# Channel banner
st.markdown(f"""
<div class="channel-banner">
    {'<img class="channel-avatar" src="' + avatar + '">' if avatar else ''}
    <div>
        <div class="channel-name">{channel_name}</div>
        <div class="channel-handle">{handle}</div>
        {'<div class="channel-country">🌍 ' + country + '</div>' if country else ''}
        <div class="channel-desc">{desc}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Stat cards
started_str = created_dt.strftime("%b %d, %Y") if created_dt else "N/A"
age_str     = f"{channel_age_years} years old" if channel_age_years else ""
st.markdown(f"""
<div class="stat-grid">
    <div class="stat-card">
        <div class="stat-label">Subscribers</div>
        <div class="stat-value">{fmt_number(subs)}</div>
        <div class="stat-sub">Total</div>
    </div>
    <div class="stat-card green">
        <div class="stat-label">Total Views</div>
        <div class="stat-value">{fmt_number(total_views)}</div>
        <div class="stat-sub">Lifetime</div>
    </div>
    <div class="stat-card orange">
        <div class="stat-label">Total Videos</div>
        <div class="stat-value">{fmt_number(total_vids)}</div>
        <div class="stat-sub">Public</div>
    </div>
    <div class="stat-card">
        <div class="stat-label">Channel Started</div>
        <div class="stat-value" style="font-size:18px;">{started_str}</div>
        <div class="stat-sub">{age_str}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Fetch videos
with st.spinner(f"Fetching uploads playlist..."):
    playlist_id, err = get_uploads_playlist_id(channel_id, api_key)

if err:
    st.error(err)
    st.stop()

limit_val = int(video_limit) if video_limit else None

st.info(f"Fetching {'last ' + str(limit_val) if limit_val else 'all'} video IDs... This may take a moment for large channels.")

with st.spinner("Fetching video IDs..."):
    video_ids, err = fetch_video_ids(playlist_id, api_key, limit=limit_val)

if err:
    st.error(err)
    st.stop()

st.success(f"Found {len(video_ids)} videos. Now fetching details...")

prog = st.progress(0.0, text="Fetching video details...")
video_details, err = fetch_video_details(video_ids, api_key, progress_bar=prog)
prog.empty()

if err:
    st.error(err)
    st.stop()

if not video_details:
    st.warning("No video data returned.")
    st.stop()

df = pd.DataFrame(video_details)
df = df.sort_values("published_at")

shorts_df = df[df["is_short"]].copy()
long_df   = df[~df["is_short"]].copy()

n_shorts = len(shorts_df)
n_long   = len(long_df)
avg_views_long   = int(long_df["views"].mean()) if not long_df.empty else 0
avg_views_short  = int(shorts_df["views"].mean()) if not shorts_df.empty else 0
avg_dur_long     = round(long_df["duration_min"].mean(), 1) if not long_df.empty else 0
avg_eng          = round(df.apply(lambda r: engagement_rate(r.views, r.likes, r.comments), axis=1).mean(), 3)

# Derived stat cards row 2
st.markdown(f"""
<div class="stat-grid">
    <div class="stat-card">
        <div class="stat-label">Long Videos</div>
        <div class="stat-value">{n_long}</div>
        <div class="stat-sub">Avg {fmt_number(avg_views_long)} views each</div>
    </div>
    <div class="stat-card">
        <div class="stat-label">Shorts</div>
        <div class="stat-value">{n_shorts}</div>
        <div class="stat-sub">Avg {fmt_number(avg_views_short)} views each</div>
    </div>
    <div class="stat-card green">
        <div class="stat-label">Avg Duration (Long)</div>
        <div class="stat-value">{avg_dur_long}<span style="font-size:14px"> min</span></div>
        <div class="stat-sub">Long videos only</div>
    </div>
    <div class="stat-card orange">
        <div class="stat-label">Avg Engagement Rate</div>
        <div class="stat-value">{avg_eng}<span style="font-size:14px">%</span></div>
        <div class="stat-sub">(likes+comments)/views</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tabs = st.tabs(["📅  Posting", "📈  Performance", "💬  Engagement", "🎬  Content", "🔤  Titles", "📋  All Videos"])

# ── TAB 1: Posting ────────────────────────────────────────────────────────────
with tabs[0]:
    st.markdown('<div class="section-header"><div class="section-dot"></div><h2>Posting Patterns</h2></div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(chart_videos_over_time(df), use_container_width=True)
    with c2:
        st.plotly_chart(chart_cumulative_videos(df), use_container_width=True)

    st.plotly_chart(chart_posting_heatmap(df), use_container_width=True)

    c3, c4 = st.columns(2)
    with c3:
        st.plotly_chart(chart_shorts_vs_long(df), use_container_width=True)
    with c4:
        # Videos per year bar
        yr_cnt = df.groupby("year").size().reset_index(name="videos").dropna()
        yr_cnt["year"] = yr_cnt["year"].astype(int).astype(str)
        fig_yr = px.bar(yr_cnt, x="year", y="videos", color_discrete_sequence=[GREEN])
        fig_yr.update_layout(**PLOTLY_THEME, title="Videos Per Year", height=340)
        st.plotly_chart(fig_yr, use_container_width=True)

# ── TAB 2: Performance ────────────────────────────────────────────────────────
with tabs[1]:
    st.markdown('<div class="section-header"><div class="section-dot"></div><h2>Performance Analysis</h2></div>', unsafe_allow_html=True)
    st.plotly_chart(chart_views_scatter(df, subs), use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(chart_avg_views_by_year(df), use_container_width=True)
    with c2:
        st.plotly_chart(chart_views_per_year_type(df), use_container_width=True)

    st.plotly_chart(chart_top_videos(df, subs, n=20), use_container_width=True)
    st.plotly_chart(chart_shorts_vs_long_performance(df), use_container_width=True)

# ── TAB 3: Engagement ─────────────────────────────────────────────────────────
with tabs[2]:
    st.markdown('<div class="section-header"><div class="section-dot"></div><h2>Engagement Deep Dive</h2></div>', unsafe_allow_html=True)
    st.plotly_chart(chart_engagement_trend(df), use_container_width=True)
    st.plotly_chart(chart_likes_comments_trend(df), use_container_width=True)

    # Engagement by type table
    c1, c2 = st.columns(2)
    with c1:
        eng_grp = df.copy()
        eng_grp["eng_rate"] = eng_grp.apply(lambda r: engagement_rate(r.views, r.likes, r.comments), axis=1)
        eng_type = eng_grp.groupby("is_short").agg(
            avg_eng=("eng_rate","mean"),
            total_likes=("likes","sum"),
            total_comments=("comments","sum"),
        ).reset_index()
        eng_type["type"] = eng_type["is_short"].map({True:"Shorts", False:"Long Videos"})
        fig_eng = px.bar(eng_type, x="type", y="avg_eng",
                         color="type", color_discrete_map={"Shorts": ACCENT, "Long Videos": GREEN})
        fig_eng.update_layout(**PLOTLY_THEME, title="Avg Engagement Rate by Type", height=340, showlegend=False)
        st.plotly_chart(fig_eng, use_container_width=True)
    with c2:
        # Comments vs views scatter
        sample = df.sample(min(len(df), 300), random_state=42)
        fig_cv = px.scatter(sample, x="views", y="comments",
                            color="is_short",
                            color_discrete_map={True: ACCENT, False: GREEN},
                            opacity=0.7, hover_name="title",
                            labels={"is_short":"Short"})
        fig_cv.update_layout(**PLOTLY_THEME, title="Comments vs Views", height=340,
                             xaxis_title="Views", yaxis_title="Comments")
        st.plotly_chart(fig_cv, use_container_width=True)

# ── TAB 4: Content ────────────────────────────────────────────────────────────
with tabs[3]:
    st.markdown('<div class="section-header"><div class="section-dot"></div><h2>Content Analysis</h2></div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(chart_duration_histogram(df), use_container_width=True)
    with c2:
        # Tags frequency
        all_tags = []
        for tags in df["tags"]:
            all_tags.extend([t.lower() for t in tags])
        if all_tags:
            tag_freq = Counter(all_tags).most_common(20)
            tf_df = pd.DataFrame(tag_freq, columns=["tag","count"])
            fig_tags = px.bar(tf_df.sort_values("count"), x="count", y="tag", orientation="h",
                              color="count", color_continuous_scale=[[0,MUTED],[1,ACCENT2]])
            fig_tags.update_layout(**PLOTLY_THEME, title="Top 20 Tags Used", height=420,
                                   yaxis=dict(tickfont=dict(size=10), categoryorder="total ascending"),
                                   coloraxis_showscale=False)
            st.plotly_chart(fig_tags, use_container_width=True)
        else:
            st.info("No tag data available for this channel.")

    # Duration vs views
    fig_dv = px.scatter(df[~df["is_short"]], x="duration_min", y="views",
                        opacity=0.65, color_discrete_sequence=[ACCENT2],
                        hover_name="title", trendline="lowess")
    fig_dv.update_layout(**PLOTLY_THEME, title="Duration vs Views (Long Videos)",
                         height=380, xaxis_title="Duration (min)", yaxis_title="Views")
    st.plotly_chart(fig_dv, use_container_width=True)

# ── TAB 5: Title Intelligence ─────────────────────────────────────────────────
with tabs[4]:
    st.markdown('<div class="section-header"><div class="section-dot"></div><h2>Title Intelligence</h2></div>', unsafe_allow_html=True)

    st.plotly_chart(chart_top_titles_by_vps(df, subs, n=25), use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        fig_top = chart_title_wordcloud_bar(df, n=20, top_only=True)
        if fig_top:
            st.plotly_chart(fig_top, use_container_width=True)
    with c2:
        fig_all = chart_title_wordcloud_bar(df, n=20, top_only=False)
        if fig_all:
            st.plotly_chart(fig_all, use_container_width=True)

    # Title length vs views
    df2 = df.copy()
    df2["title_len"] = df2["title"].str.len()
    fig_tl = px.scatter(df2, x="title_len", y="views", color="is_short",
                        color_discrete_map={True: ACCENT, False: GREEN},
                        opacity=0.65, hover_name="title", trendline="lowess",
                        labels={"is_short":"Short","title_len":"Title Length (chars)"})
    fig_tl.update_layout(**PLOTLY_THEME, title="Title Length vs Views", height=360,
                         xaxis_title="Title Length (chars)", yaxis_title="Views")
    st.plotly_chart(fig_tl, use_container_width=True)

# ── TAB 6: All Videos Table ───────────────────────────────────────────────────
with tabs[5]:
    st.markdown('<div class="section-header"><div class="section-dot"></div><h2>All Videos</h2></div>', unsafe_allow_html=True)

    col_filter1, col_filter2, col_filter3 = st.columns(3)
    with col_filter1:
        type_filter = st.selectbox("Type", ["All", "Long Videos", "Shorts"])
    with col_filter2:
        sort_by = st.selectbox("Sort by", ["Published (newest)", "Published (oldest)", "Views", "Likes", "Comments", "Engagement Rate"])
    with col_filter3:
        search_term = st.text_input("Search title", placeholder="keyword...")

    display_df = df.copy()
    display_df["engagement_rate"] = display_df.apply(
        lambda r: engagement_rate(r.views, r.likes, r.comments), axis=1)
    display_df["vps"] = (display_df["views"] / max(subs, 1)).round(4)
    display_df["published"] = display_df["published_at"].dt.strftime("%Y-%m-%d")
    display_df["type"] = display_df["is_short"].map({True:"Short", False:"Long"})

    if type_filter == "Long Videos":
        display_df = display_df[~display_df["is_short"]]
    elif type_filter == "Shorts":
        display_df = display_df[display_df["is_short"]]

    if search_term:
        display_df = display_df[display_df["title"].str.contains(search_term, case=False, na=False)]

    sort_map = {
        "Published (newest)": ("published_at", False),
        "Published (oldest)": ("published_at", True),
        "Views":              ("views", False),
        "Likes":              ("likes", False),
        "Comments":           ("comments", False),
        "Engagement Rate":    ("engagement_rate", False),
    }
    sc, sa = sort_map[sort_by]
    display_df = display_df.sort_values(sc, ascending=sa)

    st.markdown(f"<div style='font-family: Space Mono; font-size:12px; color:#6b6b7b; margin-bottom:12px;'>Showing {len(display_df)} videos</div>", unsafe_allow_html=True)

    cols_show = ["published","type","title","views","likes","comments","engagement_rate","vps","duration_min"]
    st.dataframe(
        display_df[cols_show].rename(columns={
            "published":"Date","type":"Type","title":"Title",
            "views":"Views","likes":"Likes","comments":"Comments",
            "engagement_rate":"Eng %","vps":"Views/Sub","duration_min":"Duration (min)"
        }),
        use_container_width=True,
        height=600,
        hide_index=True,
    )

    csv = display_df[cols_show].to_csv(index=False)
    st.download_button("⬇ Download CSV", csv, f"{channel_name}_videos.csv", "text/csv")
