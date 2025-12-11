import feedparser
from textblob import TextBlob
import json
import os
from datetime import datetime
import re 

# 1. SETUP: List your RSS feeds here
RSS_FEEDS = [
    "http://rss.cnn.com/rss/edition.rss",
    "http://feeds.bbci.co.uk/news/rss.xml",
    # Add more feeds here.
]

def analyze_sentiment(text):
    """
    Returns polarity (positive/negative) and subjectivity (opinion/fact).
    """
    blob = TextBlob(text)
    return blob.sentiment.polarity, blob.sentiment.subjectivity

def extract_image_from_entry(entry):
    """
    Attempts to find an image URL from various common RSS feed structures.
    """
    if 'media_content' in entry and entry.media_content:
        for media in entry.media_content:
            if 'url' in media and media.get('type', '').startswith('image'):
                return media['url']
            if 'url' in media and not media.get('type'):
                return media['url']
    if 'enclosures' in entry and entry.enclosures:
        for enclosure in entry.enclosures:
            if 'url' in enclosure and enclosure.get('type', '').startswith('image'):
                return enclosure['url']
    if 'image' in entry and 'href' in entry.image:
        return entry.image.href
    
    if 'summary' in entry:
        match = re.search(r'<img[^>]+src="([^">]+)"', entry.summary)
        if match:
            return match.group(1)
            
    return None

def extract_keywords(title_and_summary):
    """
    Extracts up to 3 strong noun phrases for filtering and image search.
    """
    try:
        blob = TextBlob(title_and_summary)
        # Get noun phrases and filter out common/short phrases
        keywords = [
            phrase.lower() for phrase in blob.noun_phrases 
            if len(phrase.split()) > 1 and len(phrase) > 5
        ][:3] 

        if not keywords:
            # Fallback to the first word if no good noun phrases are found
            keywords.append(title_and_summary.split()[0].lower())
            
        return keywords
    except Exception:
        # Emergency fallback if TextBlob analysis fails (e.g., empty string)
        return ["analysis-error"]


def fetch_and_analyze():
    articles = []
    
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            print(f"Fetching {feed_url}...")
            
            # Changed limit from 10 to 50 for more content
            for entry in feed.entries[:50]: 
                title = entry.title
                link = entry.link
                summary = getattr(entry, 'summary', '')
                
                image_url = extract_image_from_entry(entry)
                
                # Ensure text is not empty before analysis
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

    # Save to JSON file
    with open('news_data.json', 'w') as f:
        json.dump(articles, f, indent=4)
    print("News updated successfully.")

if __name__ == "__main__":
    fetch_and_analyze()
