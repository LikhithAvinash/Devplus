from sqlalchemy.orm import Session
from database import SessionLocal, engine
import models

# Create tables if they don't exist
models.Base.metadata.create_all(bind=engine)

def seed_sources():
    db = SessionLocal()
    
    sources_data = [
        # 1. News & Discussions
        {
            "name": "Hacker News",
            "url": "https://hacker-news.firebaseio.com/v0/",
            "feed_type": "API",
            "category": "News & Discussions",
            "icon": "Y"
        },
        {
            "name": "Reddit",
            "url": "https://www.reddit.com/r/learnprogramming/.rss",
            "feed_type": "RSS",
            "category": "News & Discussions",
            "icon": "reddit"
        },
        {
            "name": "Lobste.rs",
            "url": "https://lobste.rs/hottest.json",
            "feed_type": "JSON",
            "category": "News & Discussions",
            "icon": "lobster"
        },
        {
            "name": "Techmeme",
            "url": "https://www.techmeme.com/feed.xml",
            "feed_type": "RSS",
            "category": "News & Discussions",
            "icon": "techmeme"
        },
        {
            "name": "Ars Technica",
            "url": "https://feeds.arstechnica.com/arstechnica/index",
            "feed_type": "RSS",
            "category": "News & Discussions",
            "icon": "ars"
        },
        {
            "name": "Slashdot",
            "url": "http://rss.slashdot.org/Slashdot/slashdot",
            "feed_type": "RSS",
            "category": "News & Discussions",
            "icon": "slashdot"
        },
        
        # 2. Code, Tools & Products
        {
            "name": "GitHub Trending",
            "url": "https://github.com/trending",
            "feed_type": "Scraping",
            "category": "Code, Tools & Products",
            "icon": "github"
        },
        {
            "name": "Product Hunt",
            "url": "https://www.producthunt.com/feed",
            "feed_type": "RSS",
            "category": "Code, Tools & Products",
            "icon": "producthunt"
        },
        {
            "name": "The Changelog",
            "url": "https://changelog.com/feed",
            "feed_type": "RSS",
            "category": "Code, Tools & Products",
            "icon": "changelog"
        },

        # 3. Knowledge & Tutorials
        {
            "name": "Tech Blog",
            "url": "https://medium.com/feed/netflix-techblog",
            "feed_type": "RSS",
            "category": "Knowledge & Tutorials",
            "icon": "techblog"
        },
        {
            "name": "DEV.to",
            "url": "https://dev.to/api/articles",
            "feed_type": "API",
            "category": "Knowledge & Tutorials",
            "icon": "dev"
        },
        {
            "name": "HackerNoon",
            "url": "https://hackernoon.com/feed",
            "feed_type": "RSS",
            "category": "Knowledge & Tutorials",
            "icon": "hackernoon"
        }
    ]

    for source in sources_data:
        exists = db.query(models.Source).filter(models.Source.name == source["name"]).first()
        if not exists:
            new_source = models.Source(**source)
            db.add(new_source)
            print(f"Added {source['name']}")
        else:
            print(f"Skipped {source['name']} (already exists)")
    
    db.commit()
    db.close()

if __name__ == "__main__":
    seed_sources()
