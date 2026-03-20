# Reddit → Script Scraper

A minimal Streamlit app that scrapes any public Reddit post and exports two clean `.md` files — ready to paste into any AI to generate a YouTube long-form script.

## What it exports

### `post.md`
- Post title
- Subreddit, upvotes, upvote ratio, total comment count, date
- Full post body text
- Source URL

### `comments.md`
- All comments (all nested levels), sorted by upvotes descending
- Upvote count per comment + thread depth label
- **No usernames**
- Custom count — you set how many in the app

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Streamlit Cloud (free)

1. Fork or push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repo
4. Set `app.py` as the entrypoint
5. Click **Deploy**

No API keys or secrets needed.

## How to use the output

Download both files, then paste them into Claude or ChatGPT with a prompt like:

> "Here is a Reddit post and its top comments. Write a YouTube script for a 15-minute video based on this content. Use the comments as supporting opinions and reactions."
