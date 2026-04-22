# 📡 YT Channel Intelligence

A dark-themed Streamlit dashboard that gives you deep analysis of any YouTube channel — built for creators who want to understand what makes their competitors tick.

---

## What It Does

- **Channel Overview** — name, handle, subscribers, total views, total videos, channel age
- **Posting Patterns** — monthly cadence, yearly totals, day × hour heatmap, cumulative growth, Shorts vs Long ratio
- **Performance Analysis** — views/subscriber scatter, top 20 videos by views-per-sub, avg views by year & type
- **Engagement Deep Dive** — engagement rate trend, likes & comments over time, comments vs views scatter
- **Content Analysis** — duration distribution, top tags, duration vs views correlation
- **Title Intelligence** — top 25 titles by views/sub, keyword frequency in top-performing titles, title length vs views
- **All Videos Table** — filterable, sortable, downloadable CSV of every video

---

## Setup — Local

### 1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
cd YOUR_REPO
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Add your API key
Create `.streamlit/secrets.toml` (already in `.gitignore`):
```toml
YOUTUBE_API_KEY = "YOUR_API_KEY_HERE"
```

Get a free YouTube Data API v3 key at [console.cloud.google.com](https://console.cloud.google.com) → Enable **YouTube Data API v3** → Create credentials → API Key.

### 4. Run
```bash
streamlit run app.py
```

---

## Deploy on Streamlit Cloud (Free)

1. Push this repo to GitHub (the `.gitignore` protects your secrets file)
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repo
4. In **App Settings → Secrets**, add:
   ```
   YOUTUBE_API_KEY = "YOUR_API_KEY_HERE"
   ```
5. Deploy — done ✅

---

## YouTube API Quota

The free YouTube Data API v3 gives you **10,000 units/day**.

| Action | Units Used |
|---|---|
| Fetch channel info | ~3 |
| Fetch video ID list (per 50) | ~3 |
| Fetch video details (per 50) | ~5 |

A 500-video channel costs roughly **60–70 units** total. A 2,000-video channel costs ~250 units. You have plenty of headroom for daily use.

---

## Usage Tips

- Paste a channel URL like `https://youtube.com/@mkbhd` or just the handle `@mkbhd`
- For channels with 1000+ videos, use the **Fixed Options** or **Custom Number** limit to control quota usage
- The **Views/Subscriber** metric is the most important one — it normalizes for channel size and shows which videos truly over-performed
- The **Title Intelligence** tab shows you which words appear most in the top 25% of videos — this is your content research

---

## File Structure

```
├── app.py                          # Main Streamlit app
├── requirements.txt                # Python dependencies
├── .gitignore                      # Keeps secrets off GitHub
├── .streamlit/
│   ├── config.toml                 # Dark theme config
│   └── secrets.toml.template       # Template — copy and fill in
└── README.md
```
