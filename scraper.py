from apify_client import ApifyClient
from config import Config
import pandas as pd

class FacebookScraper:
    def __init__(self):
        self.client = ApifyClient(Config.APIFY_TOKEN)
        self.actor_id = "KoJrdxJCTtpon81KY" 

    def scrape(self, page_url, max_posts=5):

        print(f"Starting scrape for: {page_url} (Limit: {max_posts} posts)...")
        
        run_input = {
            "startUrls": [{"url": page_url}],
            "resultsLimit": max_posts,
            "view": "posts",  # We want posts, not just page info
        }

        run = self.client.actor(self.actor_id).call(run_input=run_input)
        dataset_items = self.client.dataset(run["defaultDatasetId"]).list_items().items
        
        print(f"Scrape complete! Found {len(dataset_items)} items.")
        return self._clean_data(dataset_items)

    def _clean_data(self, items):
        cleaned_posts = []
        for item in items:
            post = {
                "date": item.get("time", "Unknown Date"),
                "text": item.get("text", "")[:500],  # Truncate very long posts
                "likes": item.get("likes", 0),
                "comments": item.get("comments", 0),
                "shares": item.get("shares", 0),
                "url": item.get("url", "No URL"),
                "type": item.get("type", "unknown") # photo, video, etc.
            }
            # Only keep posts that have text or reasonable engagement
            if post['text'] or post['likes'] > 0:
                cleaned_posts.append(post)
        
        return cleaned_posts

if __name__ == "__main__":
    scraper = FacebookScraper()
    data = scraper.scrape("https://www.facebook.com/HethonggiaoducLyThaiTo")
    print(data)