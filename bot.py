import feedparser
from textblob import TextBlob
import json
import os
from datetime import datetime
import re # For simple keyword extraction

# 1. SETUP: List your RSS feeds here (CNN, BBC, etc.)
RSS_FEEDS = [
    "http://rss.cnn.com/rss/edition.rss",
    "http://feeds.bbci.co.uk/news/rss.xml",
    # Add more feeds here. Some feeds might include image URLs.
]

def analyze_sentiment(text):
    """
    Returns polarity (positive/negative) and subjectivity (opinion/fact).
    Subjectivity: 0.0 is very objective, 1.0 is very subjective.
    Polarity: -1.0 is negative, 1.0 is positive.
    """
    blob = TextBlob(text)
    return blob.sentiment.polarity, blob.sentiment.subjectivity

def extract_image_from_entry(entry):
    """
    Attempts to find an image URL from various common RSS feed structures.
    """
    # Check for media:content (common for images)
    if 'media_content' in entry and entry.media_content:
        for media in entry.media_content:
            if 'url' in media and media.get('type', '').startswith('image'):
                return media['url']
            if 'url' in media and not media.get('type'): # Sometimes type is missing
                return media['url']

    # Check for enclosures (another common way for podcasts/images)
    if 'enclosures' in entry and entry.enclosures:
        for enclosure in entry.enclosures:
            if 'url' in enclosure and enclosure.get('type', '').startswith('image'):
                return enclosure['url']
    
    # Check for 'image' field directly (less common but exists)
    if 'image' in entry and 'href' in entry.image:
        return entry.image.href

    # Check for img tag in summary/content (less reliable, but a fallback)
    if 'summary' in entry:
        match = re.search(r'<img[^>]+src="([^">]+)"', entry.summary)
        if match:
            return match.group(1)
            
    if 'content' in entry:
        for content_item in entry.content:
            if 'value' in content_item:
                match = re.search(r'<img[^>]+src="([^">]+)"', content_item.value)
                if match:
                    return match.group(1)

    return None

def extract_keyword_for_image(title):
    """
    Simple keyword extraction for placeholder images if no image found.
    Picks the first significant word (not a stop word).
    """
    stop_words = set("a an the is are was were be by for from to in on at with and or but if as by for of on from into near over through under up".split())
    words = re.findall(r'\b\w+\b', title.lower())
    for word in words:
        if word not in stop_words and len(word) > 3: # Ignore very short words
            return word
    return "news" # Default if no good keyword is found

def fetch_and_analyze():
    articles = []
    
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            print(f"Fetching {feed_url}...")
            
            for entry in feed.entries[:10]: # Limit to top 10 per feed for better variety & images
                title = entry.title
                link = entry.link
                summary = getattr(entry, 'summary', '')
                
                # Try to get image from feed
                image_url = extract_image_from_entry(entry)
                
                # If no image found, extract a keyword for placeholder
                image_keyword = None
                if not image_url:
                    image_keyword = extract_keyword_for_image(title)
                
                # Combine title and summary for better analysis
                full_text = f"{title} {summary}"
                
                polarity, subjectivity = analyze_sentiment(full_text)
                
                # Convert scores to readable metrics
                obj_score = int(subjectivity * 100) # Higher = More Opinionated
                if polarity > 0.1: sent_label = "Positive"
                elif polarity < -0.1: sent_label = "Negative"
                else: sent_label = "Neutral"

                article_data = {
                    "title": title,
                    "link": link,
                    "summary": summary[:200] + "..." if len(summary) > 200 else summary,
                    "source": feed.feed.get('title', 'Unknown Source'),
                    "objectivity_score": obj_score,  # Higher = More Opinionated
                    "sentiment": sent_label,
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "image_url": image_url,        # New: direct image from feed
                    "image_keyword": image_keyword # New: keyword for placeholder
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
