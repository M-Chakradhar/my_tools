# Reddit → Script Scraper

Scrapes any public Reddit post and exports two clean `.md` files — ready to paste into any AI to generate a YouTube long-form script.

## What it exports

**`post.md`** — title, subreddit, upvotes, upvote ratio, total comments, date, source URL, full post body

**`comments.md`** — all comments (all nested levels), sorted by upvotes descending, no usernames, custom count you set in the app

## Setup — Reddit API credentials (free, 2 min)

1. Go to [reddit.com/prefs/apps](https://www.reddit.com/prefs/apps)
2. Click **"Create another app"**
3. Type: **script** | Name: anything | Redirect URI: `http://localhost`
4. Copy your **client_id** (short string under the app name) and **client_secret**

## Run locally

Create `.streamlit/secrets.toml`:
```toml
REDDIT_CLIENT_ID = "your_client_id"
REDDIT_CLIENT_SECRET = "your_client_secret"
```

Then:
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Streamlit Cloud (free)

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io) → connect repo → entrypoint: `app.py`
3. Settings → Secrets → add:
```toml
REDDIT_CLIENT_ID = "your_client_id"
REDDIT_CLIENT_SECRET = "your_client_secret"
```
4. Deploy — done

## Prompt to use with downloaded files

> "Here is a Reddit post and its top comments. Write a YouTube script for a 15-minute video. Use the post as the core story and pull the comments as supporting opinions and reactions."
