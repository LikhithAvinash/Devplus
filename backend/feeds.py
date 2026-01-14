import os
import requests
import feedparser
from bs4 import BeautifulSoup
from typing import List
from dotenv import load_dotenv
from fastapi import HTTPException
from datetime import datetime, timezone

# Load environment variables regardless of where this module lives.
# Try repo root, current dir, then default dotenv search which also
# looks at actual environment (useful once docker compose injects vars).
_BASE_DIR = os.path.dirname(__file__)
_ENV_CANDIDATES = [
    os.path.join(_BASE_DIR, '..', '.env'),
    os.path.join(_BASE_DIR, '.env'),
    os.path.join(os.getcwd(), '.env'),
]
for _candidate in _ENV_CANDIDATES:
    if os.path.exists(_candidate):
        load_dotenv(_candidate)
        break
else:
    load_dotenv()

# API Keys from environment
DEVTO_API_KEY = os.getenv("DEVTO_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USERNAME = os.getenv("REDDIT_USERNAME")
PRODUCT_HUNT_API_KEY = os.getenv("Product_hunt_API_Key")
PRODUCT_HUNT_API_SECRET = os.getenv("Product_hunt_API_Secret")


def fetch_rss(url: str) -> List[dict]:
    """Fetch and parse RSS/Atom feeds."""
    try:
        # Fetch with requests first using browser-like headers
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/rss+xml, application/xml, application/atom+xml, text/xml, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate",
            "Connection":  "keep-alive"
        }
        
        # Fetch the feed content
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        # Parse the fetched content
        parsed = feedparser.parse(response.content)
        
        # Check if parsing was successful
        if parsed.bozo and not parsed.entries:
            raise HTTPException(status_code=502, detail=f"Failed to parse RSS feed: {url}")

        items = []
        for entry in parsed.entries[: 30]: 
            items.append({
                "title": entry.get("title"),
                "link": entry.get("link"),
                "published": entry.get("published", entry.get("updated")),
                "summary": clean_html(entry.get("summary", entry.get("description", ""))),
            })
        return items
    except HTTPException:
        raise
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch RSS feed {url}: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"RSS fetch error for {url}: {str(e)}")


def clean_html(text: str) -> str:
    """Remove HTML tags and clean up text for display."""
    if not text:
        return ""
    soup = BeautifulSoup(text, "html.parser")
    return soup.get_text(separator=" ", strip=True)[:500]


def parse_datetime(date_str: str) -> datetime:
    """Parse various datetime formats to datetime object."""
    if not date_str:
        return datetime.min.replace(tzinfo=timezone.utc)
    
    try:
        # Try ISO format first
        if 'T' in date_str:
            # Handle ISO format with or without timezone
            if date_str.endswith('Z'):
                date_str = date_str[:-1] + '+00:00'
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        
        # Try common RSS formats
        from email.utils import parsedate_to_datetime
        try:
            return parsedate_to_datetime(date_str)
        except:
            pass
        
        # Fallback - try dateutil if available
        try:
            from dateutil import parser
            return parser.parse(date_str)
        except:
            pass
            
    except:
        pass
    
    return datetime.min.replace(tzinfo=timezone.utc)


def calculate_hot_score(item: dict, gravity: float = 1.8) -> float:
    """
    Calculate hot score using algorithm similar to Hacker News/Reddit.
    Score = Upvotes / (Age + 2)^Gravity
    """
    # Get upvotes from extra or parse from summary
    upvotes = 0
    if item.get("extra") and item["extra"].get("score"):
        upvotes = item["extra"]["score"]
    else:
        # Try to parse from summary
        summary = item.get("summary", "")
        import re
        match = re.search(r'(?:⬆|↑|Score:?)\s*(\d+)', summary)
        if match:
            upvotes = int(match.group(1))
    
    # Get age in hours
    published = item.get("published")
    if published:
        pub_dt = parse_datetime(published)
        now = datetime.now(timezone.utc)
        age_hours = max(0, (now - pub_dt).total_seconds() / 3600)
    else:
        age_hours = 24  # Default to 24 hours if no timestamp
    
    # Calculate score
    score = upvotes / ((age_hours + 2) ** gravity)
    return score


def sort_items(items: List[dict], sort_by: str = "hot") -> List[dict]:
    """Sort items by 'hot' (score-based) or 'new' (time-based)."""
    if sort_by == "new":
        # Sort by published date, newest first
        return sorted(
            items,
            key=lambda x: parse_datetime(x.get("published", "")),
            reverse=True
        )
    else:  # hot
        # Sort by hot score
        return sorted(
            items,
            key=lambda x: calculate_hot_score(x),
            reverse=True
        )


def fetch_json(url: str) -> List[dict]:
    """Fetch JSON feeds like Lobste.rs."""
    try:
        resp = requests.get(url, headers={"User-Agent": "DevPulse/1.0"}, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        # Handle lobste.rs style list
        if isinstance(data, list):
            items = []
            for entry in data[:30]:
                items.append({
                    "title": entry.get("title"),
                    "link": entry.get("url") or entry.get("short_id_url"),
                    "published": entry.get("created_at") if isinstance(entry.get("created_at"), str) else None,
                    "summary": entry.get("description") or entry.get("comments_url", ""),
                })
            return items

        # If the structure is unknown, try to coerce
        if isinstance(data, dict) and "items" in data:
            items = []
            for entry in data.get("items", [])[:30]:
                items.append({
                    "title": entry.get("title"),
                    "link": entry.get("url") or entry.get("link"),
                    "published": entry.get("published"),
                    "summary": entry.get("summary", entry.get("description", "")),
                })
            return items

        raise HTTPException(status_code=502, detail=f"Unsupported JSON feed structure for {url}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"JSON fetch error for {url}: {str(e)}")


def fetch_hackernews(api_base: str) -> List[dict]:
    """Fetch top stories from Hacker News API."""
    try:
        top_url = api_base.rstrip("/") + "/topstories.json"
        resp = requests.get(top_url, headers={"User-Agent": "DevPulse/1.0"}, timeout=15)
        resp.raise_for_status()
        ids = resp.json()[:25]  # Limit to 25 for performance

        items = []
        for story_id in ids:
            try:
                it = requests.get(f"{api_base}item/{story_id}.json", timeout=5).json()
                if not it:
                    continue
                title = it.get("title")
                url = it.get("url") or f"https://news.ycombinator.com/item?id={story_id}"
                score = it.get("score", 0)
                # Convert Unix timestamp to ISO format
                timestamp = it.get("time")
                published = None
                if timestamp:
                    published = datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()
                items.append({
                    "title": f"{title}",
                    "link": url,
                    "published": published,
                    "summary": f"Score: {score} points | {it.get('descendants', 0)} comments",
                    "extra": {"score": score, "comments": it.get('descendants', 0), "timestamp": timestamp}
                })
            except:
                continue
        return items
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Hacker News fetch error: {str(e)}")


def fetch_devto() -> List[dict]:
    """Fetch articles from DEV.to API."""
    try:
        headers = {"User-Agent": "DevPulse/1.0"}
        if DEVTO_API_KEY:
            headers["api-key"] = DEVTO_API_KEY
        
        resp = requests.get(
            "https://dev.to/api/articles?per_page=30",
            headers=headers,
            timeout=15
        )
        resp.raise_for_status()
        articles = resp.json()

        items = []
        for article in articles[:30]:
            items.append({
                "title": article.get("title"),
                "link": article.get("url"),
                "published": article.get("published_at") or article.get("created_at"),
                "summary": article.get("description", ""),
            })
        return items
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"DEV.to fetch error: {str(e)}")


def fetch_reddit(subreddit: str = "programming") -> List[dict]:
    """Fetch posts from Reddit using OAuth."""
    try:
        # Reddit requires OAuth for reliable API access
        if REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET:
            # Get OAuth token
            auth = requests.auth.HTTPBasicAuth(REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET)
            data = {"grant_type": "client_credentials"}
            headers = {"User-Agent": "DevPulse/1.0"}
            
            token_resp = requests.post(
                "https://www.reddit.com/api/v1/access_token",
                auth=auth,
                data=data,
                headers=headers,
                timeout=10
            )
            token_resp.raise_for_status()
            token = token_resp.json().get("access_token")
            
            # Fetch posts with OAuth
            headers["Authorization"] = f"Bearer {token}"
            resp = requests.get(
                f"https://oauth.reddit.com/r/{subreddit}/hot?limit=25",
                headers=headers,
                timeout=15
            )
            resp.raise_for_status()
            posts = resp.json().get("data", {}).get("children", [])
        else:
            # Fallback to public JSON endpoint (less reliable, rate limited)
            headers = {"User-Agent": "DevPulse/1.0"}
            resp = requests.get(
                f"https://www.reddit.com/r/{subreddit}/hot.json?limit=25",
                headers=headers,
                timeout=15
            )
            resp.raise_for_status()
            posts = resp.json().get("data", {}).get("children", [])

        items = []
        for post in posts:
            p = post.get("data", {})
            if p.get("stickied"):  # Skip stickied posts
                continue
            # Convert Unix timestamp to ISO format
            timestamp = p.get("created_utc")
            published = None
            if timestamp:
                published = datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()
            score = p.get('score', 0)
            comments = p.get('num_comments', 0)
            items.append({
                "title": p.get("title"),
                "link": f"https://reddit.com{p.get('permalink')}",
                "published": published,
                "summary": f"⬆ {score} | 💬 {comments} comments",
                "extra": {"score": score, "comments": comments, "timestamp": timestamp}
            })
        return items
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Reddit fetch error: {str(e)}")


def fetch_github_trending(url: str) -> List[dict]:
    """Scrape GitHub Trending page."""
    try:
        headers = {"User-Agent": "DevPulse/1.0"}
        if GITHUB_TOKEN:
            headers["Authorization"] = f"token {GITHUB_TOKEN}"
        
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        items = []

        # GitHub trending page structure - find repository rows
        rows = soup.select("article.Box-row")
        
        for row in rows[:25]:
            # Get repo name from the h2 > a element
            title_elem = row.select_one("h2 a")
            if not title_elem:
                continue
            
            href = title_elem.get("href", "")
            # Clean up the repo name
            repo_name = " / ".join(title_elem.get_text(strip=True).split())
            link = f"https://github.com{href}" if href else ""
            
            # Get description
            desc_elem = row.select_one("p")
            description = desc_elem.get_text(strip=True) if desc_elem else ""
            
            # Get stars and language
            stars_elem = row.select_one("a[href$='/stargazers']")
            stars = stars_elem.get_text(strip=True) if stars_elem else ""
            
            lang_elem = row.select_one("[itemprop='programmingLanguage']")
            lang = lang_elem.get_text(strip=True) if lang_elem else ""
            
            summary = f"{description[:200]}..." if len(description) > 200 else description
            if lang or stars:
                summary = f"{'🔤 ' + lang + ' | ' if lang else ''}{'⭐ ' + stars if stars else ''}\n{summary}"
            
            items.append({
                "title": repo_name,
                "link": link,
                "published": None,
                "summary": summary,
            })
        
        if not items:
            raise HTTPException(status_code=502, detail="Could not parse GitHub Trending page")
        return items
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"GitHub Trending fetch error: {str(e)}")


def fetch_product_hunt() -> List[dict]:
    """Fetch products from Product Hunt GraphQL API using OAuth2."""
    try:
        if not PRODUCT_HUNT_API_KEY or not PRODUCT_HUNT_API_SECRET:
            # Fallback to RSS if no API credentials
            return fetch_rss("https://www.producthunt.com/feed")
        
        # Step 1: Get OAuth2 access token using client credentials
        token_resp = requests.post(
            "https://api.producthunt.com/v2/oauth/token",
            json={
                "client_id": PRODUCT_HUNT_API_KEY,
                "client_secret": PRODUCT_HUNT_API_SECRET,
                "grant_type": "client_credentials"
            },
            headers={"Content-Type": "application/json"},
            timeout=15
        )
        token_resp.raise_for_status()
        access_token = token_resp.json().get("access_token")
        
        if not access_token:
            # Fallback to RSS if token retrieval fails
            return fetch_rss("https://www.producthunt.com/feed")
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "User-Agent": "DevPulse/1.0"
        }
        
        # GraphQL query to get today's posts
        query = """
        {
            posts(first: 20) {
                edges {
                    node {
                        id
                        name
                        tagline
                        url
                        votesCount
                        createdAt
                    }
                }
            }
        }
        """
        
        resp = requests.post(
            "https://api.producthunt.com/v2/api/graphql",
            headers=headers,
            json={"query": query},
            timeout=15
        )
        resp.raise_for_status()
        data = resp.json()
        
        # Check for GraphQL errors
        if "errors" in data:
            # Fallback to RSS on GraphQL errors
            return fetch_rss("https://www.producthunt.com/feed")
        
        posts = data.get("data", {}).get("posts", {}).get("edges", [])
        
        items = []
        for edge in posts:
            node = edge.get("node", {})
            items.append({
                "title": node.get("name"),
                "link": node.get("url"),
                "published": node.get("createdAt"),
                "summary": f"⬆ {node.get('votesCount', 0)} votes | {node.get('tagline', '')}",
            })
        return items if items else fetch_rss("https://www.producthunt.com/feed")
    except HTTPException:
        raise
    except Exception as e:
        # Fallback to RSS on any error
        try:
            return fetch_rss("https://www.producthunt.com/feed")
        except:
            raise HTTPException(status_code=502, detail=f"Product Hunt fetch error: {str(e)}")


def fetch_feed_for_source(source: dict) -> List[dict]:
    """Main dispatcher to fetch feed based on source type."""
    feed_type = (source.get("feed_type") or "").lower()
    url = source.get("url", "")
    name = source.get("name", "").lower()

    if not url and feed_type not in ["api", "graphql"]:
        raise HTTPException(status_code=400, detail="Source has no URL")

    # Hacker News
    if "hacker" in name and "news" in name:
        return fetch_hackernews(url)
    
    # Reddit
    if "reddit" in name:
        # Check for custom subreddit passed from API
        if source.get("custom_subreddit"):
            subreddit = source["custom_subreddit"]
        # Extract subreddit from name or URL
        elif "r/" in name:
            subreddit = name.split("r/")[1].split()[0].strip(",")
        elif "r/" in url:
            subreddit = url.split("r/")[1].split("/")[0]
        else:
            subreddit = "learnprogramming"  # Default subreddit
        return fetch_reddit(subreddit)
    
    # GitHub Trending
    if "github" in name and "trending" in name:
        return fetch_github_trending(url)
    
    # Product Hunt
    if "product" in name and "hunt" in name:
        return fetch_product_hunt()
    
    # DEV.to
    if "dev.to" in name or "devto" in name:
        return fetch_devto()
    
    # RSS feeds
    if feed_type == "rss":
        return fetch_rss(url)
    
    # JSON feeds (like Lobste.rs)
    if feed_type == "json":
        return fetch_json(url)
    
    # API type - try to detect which API
    if feed_type == "api":
        if "dev.to" in url:
            return fetch_devto()
        if "hacker" in url:
            return fetch_hackernews(url)
    
    # GraphQL
    if feed_type == "graphql":
        if "producthunt" in url:
            return fetch_product_hunt()
        raise HTTPException(status_code=501, detail="GraphQL source not supported")
    
    # Scraping
    if feed_type == "scraping":
        if "github" in url:
            return fetch_github_trending(url)
        raise HTTPException(status_code=501, detail="Scraping source not supported")

    # Fallback: try RSS first, then JSON
    try:
        return fetch_rss(url)
    except Exception:
        try:
            return fetch_json(url)
        except Exception:
            raise HTTPException(status_code=502, detail=f"Could not fetch feed from {url}")
