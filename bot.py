import feedparser
from textblob import TextBlob
import json
from datetime import datetime
import re 

# Set your desired limit here for LOTS of articles.
ARTICLE_LIMIT = 50 

# --- Inside your bot.py file ---

RSS_FEEDS = [
    # Existing Feeds
    "http://rss.cnn.com/rss/edition.rss",
    "http://feeds.bbci.co.uk/news/rss.xml",
    "https://www.nytimes.com/svc/collections/v1/publish/https://www.nytimes.com/section/world/rss.xml",
    "https://www.theguardian.com/world/rss",
    
    # NEW: Highly Objective Global Feeds
    "http://feeds.reuters.com/reuters/topNews",        # Reuters - Top News
    "http://hosted.ap.org/lineups/TOPHEADS-rss_2.0.xml" # AP News - Top Headlines (A known working, though older, AP feed)
]

def strip_html_tags(text):
    """
    Guaranteed method to strip all HTML tags and entities by first
    re-encoding the string to neutralize complex/malformed characters.
    """
    if not text:
        return ""
    
    # 1. Unescape HTML entities (e.g., &amp; -> &)
    import html 
    unescaped_text = html.unescape(text) 
    
    # 2. Re-encode/decode to neutralize non-standard encoding and line breaks
    neutral_text = unescaped_text.encode('ascii', 'ignore').decode('ascii')

    # 3. Use Regex to strip all remaining HTML tags
    clean = re.compile('<.*?>')
    cleaned_text = re.sub(clean, '', neutral_text)
    
    # 4. Strip any remaining leading/trailing whitespace
    return cleaned_text.strip()

def analyze_sentiment(text):
    """Returns polarity (positive/negative) and subjectivity (opinion/fact)."""
    try:
        blob = TextBlob(text)
        return blob.sentiment.polarity, blob.sentiment.subjectivity
    except Exception:
        return 0, 0 

def extract_image_from_entry(entry):
    """Attempts to find an image URL from various common RSS feed structures."""
    if 'media_content' in entry and entry.media_content:
        for media in entry.media_content:
            if 'url' in media and media.get('type', '').startswith('image'):
                return media['url']
    if 'enclosures' in entry and entry.enclosures:
        for enclosure in entry.enclosures:
            if 'url' in enclosure and enclosure.get('type', '').startswith('image'):
                return enclosure['url']
    
    for key in ['summary', 'content']:
        if key in entry:
            content = entry[key]
            if isinstance(content, list):
                content = content[0].get('value', '')
            match = re.search(r'<img[^>]+src="([^">]+)"', content)
            if match:
                return match.group(1)
    return None

def extract_keywords(title_and_summary):
    """Extracts up to 3 strong noun phrases for filtering and image search."""
    try:
        blob = TextBlob(title_and_summary)
        keywords = [
            phrase.lower() for phrase in blob.noun_phrases 
            if len(phrase.split()) > 1 and len(phrase) > 5
        ][:3] 
        if not keywords:
            first_word = title_and_summary.split()[0].lower()
            return [first_word] if len(first_word) > 3 else ["news"]
        return keywords
    except Exception:
        return ["news"]

def fetch_and_analyze():
    articles = []
    
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            print(f"Fetching {feed_url}...")
            
            for entry in feed.entries[:ARTICLE_LIMIT]: 
                title = getattr(entry, 'title', 'No Title')
                link = getattr(entry, 'link', '#')
                summary = strip_html_tags(getattr(entry, 'summary', ''))
                
                image_url = extract_image_from_entry(entry)
                
                full_text = f"{title} {summary}" if title or summary else "No content"
                
                keywords = extract_keywords(full_text)
                polarity, subjectivity = analyze_sentiment(full_text)
                
                obj_score = int(subjectivity * 100)
                if polarity > 0.1: sent_label = "Positive"
                elif polarity < -0.1: sent_label = "Negative"
                else: sent_label = "Neutral"

                article_data = {
                    "title": title,
                    "link": link,
                    "summary": summary[:200] + "..." if len(summary) > 200 else summary,
                    "source": feed.feed.get('title', 'Unknown Source'),
                    "objectivity_score": obj_score,
                    "sentiment": sent_label,
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "image_url": image_url,
                    "keywords": keywords
                }
                articles.append(article_data)
        except Exception as e:
            print(f"Error fetching {feed_url}: {e}")

    with open('news_data.json', 'w') as f:
        json.dump(articles, f, indent=4)
    print("News updated successfully.")

if __name__ == "__main__":
    fetch_and_analyze()
