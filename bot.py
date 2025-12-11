import feedparser
from textblob import TextBlob
import json
import os
from datetime import datetime

# 1. SETUP: List your RSS feeds here (CNN, BBC, etc.)
RSS_FEEDS = [
    "http://rss.cnn.com/rss/edition.rss",
    "http://feeds.bbci.co.uk/news/rss.xml",
    # Add more feeds here
]

def analyze_sentiment(text):
    """
    Returns polarity (positive/negative) and subjectivity (opinion/fact).
    Subjectivity: 0.0 is very objective, 1.0 is very subjective.
    Polarity: -1.0 is negative, 1.0 is positive.
    """
    blob = TextBlob(text)
    return blob.sentiment.polarity, blob.sentiment.subjectivity

def fetch_and_analyze():
    articles = []
    
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            print(f"Fetching {feed_url}...")
            
            for entry in feed.entries[:5]: # Limit to top 5 per feed to keep it fast
                title = entry.title
                link = entry.link
                summary = getattr(entry, 'summary', '')
                
                # Combine title and summary for better analysis
                full_text = f"{title} {summary}"
                
                polarity, subjectivity = analyze_sentiment(full_text)
                
                # Convert scores to readable metrics
                # Subjectivity: 0 (Fact) -> 100 (Opinion)
                obj_score = int(subjectivity * 100) 
                # Sentiment: converted to a simpler label
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
                    "date": datetime.now().strftime("%Y-%m-%d")
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
