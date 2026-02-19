from apify_client import ApifyClient
from config import Config
from datetime import datetime
import pandas as pd

class FacebookScraper:
    def __init__(self):
        self.client = ApifyClient(Config.APIFY_TOKEN)
        # Using the standard Facebook Posts Scraper
        self.actor_id = Config.APIFY_ACTOR_ID 

    def scrape(self, page_url, max_posts=10, start_date=None, end_date=None):
        """
        Scrapes posts and filters by date and limit.
        """
        print(f"🕵️  Starting scrape for: {page_url} (Limit: {max_posts})...")
        
        # We fetch slightly more than requested to ensure we have enough after date filtering
        # but cap it to avoid huge costs (e.g., fetch max 30 if user asked for 20)
        fetch_limit = max_posts + 5
        
        run_input = {
            "startUrls": [{"url": page_url}],
            "resultsLimit": fetch_limit,
            "view": "posts",
        }

        # Run Actor
        run = self.client.actor(self.actor_id).call(run_input=run_input)
        
        # Fetch results
        dataset_items = self.client.dataset(run["defaultDatasetId"]).list_items().items
        
        print(f"✅ Raw items fetched: {len(dataset_items)}")
        
        # Clean and Filter (This is where your error was likely happening)
        # We must pass all 3 arguments: max_posts, start_date, end_date
        cleaned_posts = self._clean_and_filter(dataset_items, max_posts, start_date, end_date)
        
        return cleaned_posts

    def _determine_format(self, item):
        """
        Analyzes raw Apify data to determine if post is Image, Reel, Video, or Text.
        """
        # Check explicit flags often provided by scrapers
        if item.get("isReel"):
            return "Reel 🎬"
        
        # Check attachments
        attachments = item.get("attachments", [])
        if attachments:
            # Look at the first attachment type
            media_type = attachments[0].get("type", "").lower() # e.g., 'photo', 'video_inline'
            
            if "video" in media_type:
                return "Video 📹"
            if "photo" in media_type or "image" in media_type:
                return "Image 🖼️"
        
        # Check if it has a video URL but wasn't caught above
        if item.get("videoUrl"):
            return "Video 📹"
            
        # If it has text but no media
        if item.get("text"):
            return "Text Only 📝"
            
        return "Link/Shared 🔗"

    def _clean_and_filter(self, items, max_posts, start_date, end_date):
        cleaned = []
        
        for item in items:
            # 1. Parse Date
            try:
                # Apify usually returns ISO strings: "2023-10-27T10:00:00.000Z"
                post_date_str = item.get("time")
                if not post_date_str:
                    continue
                
                # Convert to datetime object (ignoring timezone for simple comparison)
                post_date = datetime.fromisoformat(post_date_str.replace("Z", "+00:00")).date()
            except ValueError:
                continue

            # 2. Apply Date Filter (if provided)
            if start_date and post_date < start_date:
                continue
            if end_date and post_date > end_date:
                continue

            # 3. Determine Format
            post_format = self._determine_format(item)

            # 4. Structure Data
            post = {
                "date": str(post_date),
                "format": post_format,
                "text": item.get("text", "")[:500],
                "likes": item.get("likes", 0),
                "comments": item.get("comments", 0),
                "shares": item.get("shares", 0),
                "url": item.get("url", "No URL")
            }
            
            # Filter garbage posts (no text/likes)
            if post['text'] or post['likes'] > 0:
                cleaned.append(post)

        # 5. Apply Count Limit (after date filtering)
        return cleaned[:max_posts]

if __name__ == "__main__":
    # Test
    scraper = FacebookScraper()
    # Test with a date range
    start = datetime(2023, 1, 1).date()
    end = datetime.now().date()
    print(scraper.scrape("https://www.facebook.com/airbnb", max_posts=3, start_date=start, end_date=end))