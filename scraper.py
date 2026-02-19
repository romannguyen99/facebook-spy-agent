from apify_client import ApifyClient
from config import Config
from datetime import datetime
import pandas as pd

class FacebookScraper:
    def __init__(self):
        self.client = ApifyClient(Config.APIFY_TOKEN)
        self.actor_id = "KoJrdxJCTtpon81KY" 

    # Scrape posts from a Facebook page URL with optional date and limit filtering
    def scrape(self, page_url, max_posts=5, start_date=None, end_date=None):

        print(f"Starting scrape for: {page_url} (Limit: {max_posts} posts)...")
        
        # Fetch slightly more than requested to ensure we have enough after date filtering
        fetch_litmit = max_posts + 5
        
        run_input = {
            "startUrls": [{"url": page_url}],
            "resultsLimit": fetch_litmit,
            "view": "posts",  # We want posts, not just page info
        }

        run = self.client.actor(self.actor_id).call(run_input=run_input)
        dataset_items = self.client.dataset(run["defaultDatasetId"]).list_items().items
        
        print(f"Scrape complete! Found {len(dataset_items)} items.")
        return self._clean_data(dataset_items)
    
    # Determine format of the item (e.g. post, reel, image)
    def _determine_format(self, item):
        if item.get("isReel"):
            return "Reel"
        
        attachements = item.get("attachments", [])
        if attachements:
            media_types = attachements[0].get("type", "").lower() # e.g. "photo", "video"
            
            if "video" in media_types:
                return "Video"
            if "photo" in media_types or "image" in media_types:
                return "Image"
        
        # Check if it has a video URL but wasn't caught above
        if item.get("videoUrl"):
            return "Video"
            
        # If it has text but no media
        if item.get("text"):
            return "Text Only"
            
        return "Link/Shared"      

    def _clean_data(self, items, max_posts, start_date, end_date):
        cleaned_posts = []
        for item in items:
            # 1. Basic validation and filtering
            try:
                # Apify usually returns ISO strings: "2026-01-01T10:00:00.000Z"
                post_date_str = item.get("time")
                if not post_date_str:
                    continue  # Skip if no date

                # Convert to datetime object for filtering (Vietnam timezone)
                post_date = datetime.fromisoformat(post_date_str.replace("Z", "+07:00")).date()
            except ValueError:
                continue  # Skip if date format is invalid

            # 2. Date filtering
            if start_date and post_date < start_date:
                continue
            if end_date and post_date > end_date:
                continue

            # 3. Format determination
            post_format = self._determine_format(item)

            # 4. Construct cleaned post dict
            post = {
                "date": str(post_date),
                "format": post_format,
                "text": item.get("text", "")[:500],  # Truncate very long posts
                "likes": item.get("likes", 0),
                "comments": item.get("comments", 0),
                "shares": item.get("shares", 0),
                "url": item.get("url", "No URL"),
            }

            # Only keep posts that have text or reasonable engagement
            if post['text'] or post['likes'] > 0:
                cleaned_posts.append(post)
        
        return cleaned_posts[:max_posts]

if __name__ == "__main__":
    # Test
    scraper = FacebookScraper()

    # Test with a date range
    start = datetime(2023, 1, 1).date()
    end = datetime.now().date()
    print(scraper.scrape("https://www.facebook.com/HethonggiaoducLyThaiTo", max_posts=3, start_date=start, end_date=end))