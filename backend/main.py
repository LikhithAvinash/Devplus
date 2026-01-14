from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import models, schemas, auth, database
from database import engine
import os
import json

# Feeds
import feeds

# Redis for caching
try:
    import redis
    REDIS_URL = os.getenv("REDIS_URL")
    if REDIS_URL:
        redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        print("✅ Redis connected!")
    else:
        redis_client = None
        print("⚠️ No REDIS_URL found, caching disabled")
except Exception as e:
    redis_client = None
    print(f"⚠️ Redis connection failed: {e}")

# Create tables
models.Base.metadata.create_all(bind=engine)

def seed_if_empty():
    """Seed the database with sources if it's empty"""
    db = database.SessionLocal()
    try:
        # Check if sources exist
        count = db.query(models.Source).count()
        if count == 0:
            print("📦 Database is empty, seeding sources...")
            
            sources_data = [
                # News & Discussions
                {"name": "Hacker News", "url": "https://hacker-news.firebaseio. com/v0/", "feed_type": "API", "category": "News & Discussions", "icon": "Y"},
                {"name": "Reddit", "url": "https://www.reddit.com/r/learnprogramming/. rss", "feed_type": "RSS", "category": "News & Discussions", "icon": "reddit"},
                {"name": "Lobste.rs", "url": "https://lobste.rs/hottest. json", "feed_type": "JSON", "category": "News & Discussions", "icon": "lobster"},
                {"name": "Techmeme", "url": "https://www.techmeme.com/feed. xml", "feed_type": "RSS", "category": "News & Discussions", "icon": "techmeme"},
                {"name":  "Ars Technica", "url": "https://feeds.arstechnica.com/arstechnica/index", "feed_type": "RSS", "category": "News & Discussions", "icon": "ars"},
                {"name": "Slashdot", "url": "http://rss.slashdot.org/Slashdot/slashdot", "feed_type": "RSS", "category": "News & Discussions", "icon":   "slashdot"},
                
                # Code, Tools & Products
                {"name": "GitHub Trending", "url": "https://github.com/trending", "feed_type": "Scraping", "category": "Code, Tools & Products", "icon": "github"},
                {"name": "Product Hunt", "url": "https://www.producthunt.com/feed", "feed_type": "RSS", "category": "Code, Tools & Products", "icon": "producthunt"},
                {"name":   "The Changelog", "url": "https://changelog.com/feed", "feed_type": "RSS", "category":   "Code, Tools & Products", "icon": "changelog"},
                
                # Knowledge & Tutorials
                {"name": "Tech Blog", "url": "https://medium.com/feed/netflix-techblog", "feed_type": "RSS", "category":   "Knowledge & Tutorials", "icon": "techblog"},
                {"name":  "DEV.to", "url": "https://dev.to/api/articles", "feed_type":  "API", "category": "Knowledge & Tutorials", "icon": "dev"},
                {"name": "HackerNoon", "url": "https://hackernoon.com/feed", "feed_type": "RSS", "category": "Knowledge & Tutorials", "icon": "hackernoon"}
            ]
            
            for source in sources_data:
                new_source = models.Source(**source)
                db.add(new_source)
                print(f"  ✅ Added {source['name']}")
            
            db.commit()
            print("✨ Seeding complete!")
        else:
            print(f"✅ Database already has {count} sources")
    except Exception as e:
        print(f"❌ Error seeding database: {e}")
    finally:
        db.close()

# Run seeding on startup
seed_if_empty()

app = FastAPI(title="DevPulse API")

# CORS Setup
origins = [
    "http://localhost:5173", # Vite default port
    "http://localhost:3000",
    "https://agg-frontend-9244.onrender.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/register", response_model=schemas.UserResponse)
def register(user: schemas.UserCreate, db: Session = Depends(database. get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    db_email = db.query(models. User).filter(models.User. email == user.email).first()
    if db_email: 
        raise HTTPException(status_code=400, detail="Email already registered")

    salt = auth.generate_salt()
    hashed_password = auth.hash_password(user.password, salt)
    
    new_user = models.User(
        username=user.username,
        email=user.email,
        password_hash=hashed_password,
        salt=salt
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/login", response_model=schemas.Token)
def login(user_credentials: schemas.UserLogin, db: Session = Depends(database. get_db)):
    user = db.query(models.User).filter(models.User.username == user_credentials.username).first()
    
    if not user or not auth. verify_password(user_credentials. password, user.salt, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = auth.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/me", response_model=schemas.UserResponse)
def read_users_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user

@app.get("/sources", response_model=list[schemas.SourceResponse])
def get_sources(db: Session = Depends(database. get_db)):
    return db.query(models.Source).order_by(models.Source. id).all()


# ============ SUBREDDIT PREFERENCE ENDPOINTS ============

@app. get("/subreddit")
def get_subreddit_preference(
    current_user: models.User = Depends(auth. get_current_user)
):
    """Get user's preferred subreddit"""
    return {"subreddit": current_user. preferred_subreddit or "learnprogramming"}


@app.put("/subreddit")
def update_subreddit_preference(
    data: schemas.SubredditUpdate,
    current_user: models.User = Depends(auth. get_current_user),
    db: Session = Depends(database.get_db)
):
    """Update user's preferred subreddit"""
    # Clean the subreddit name (remove r/ prefix if present, strip spaces)
    subreddit = data.subreddit.strip()
    if subreddit.startswith("r/"):
        subreddit = subreddit[2:]
    subreddit = subreddit.strip()
    
    if not subreddit:
        raise HTTPException(status_code=400, detail="Subreddit cannot be empty")
    
    current_user.preferred_subreddit = subreddit
    db. commit()
    return {"subreddit": subreddit, "message": "Subreddit preference updated"}


@app.get("/feeds/{source_id}", response_model=list[schemas. FeedItemResponse])
def get_feed(
    source_id: int, 
    sort: str = "hot", 
    subreddit: str = None,
    db: Session = Depends(database. get_db)
):
    # Create cache key
    cache_key = f"feed:{source_id}:{sort}:{subreddit or 'default'}"
    
    # Try to get from cache
    if redis_client:
        try:
            cached = redis_client.get(cache_key)
            if cached: 
                print(f"✅ Cache HIT for {cache_key}")
                return json.loads(cached)
        except Exception as e:
            print(f"⚠️ Cache read error: {e}")
    
    # Cache miss - fetch from source
    print(f"❌ Cache MISS for {cache_key}")
    src = db.query(models.Source).filter(models.Source.id == source_id).first()
    if not src:
        raise HTTPException(status_code=404, detail="Source not found")

    # Build a simple dict to pass to feed fetcher
    source = {"name": src.name, "url":  src.url, "feed_type": src.feed_type}
    
    # If this is Reddit and a custom subreddit is provided, use it
    if "reddit" in src.name. lower() and subreddit:
        source["custom_subreddit"] = subreddit
    
    items = feeds.fetch_feed_for_source(source)

    # tag items with source name for frontend
    for it in items:
        it.setdefault("source", src.name)

    # Sort items
    items = feeds.sort_items(items, sort)

    # Store in cache for 5 minutes
    if redis_client:
        try:
            redis_client.setex(cache_key, 300, json.dumps(items))
            print(f"💾 Cached {cache_key}")
        except Exception as e: 
            print(f"⚠️ Cache write error: {e}")
    
    return items


@app.get("/feeds", response_model=list[schemas. FeedItemResponse])
def get_all_feeds(sort: str = "hot", category:  str = None, db: Session = Depends(database. get_db)):
    """Aggregate feed items from all enabled sources or a specific category.  
    Returns a combined list sorted together by hot/new algorithm."""
    
    # Create cache key
    cache_key = f"feeds: all:{sort}:{category or 'all'}"
    
    # Try to get from cache
    if redis_client:
        try: 
            cached = redis_client.get(cache_key)
            if cached:
                print(f"✅ Cache HIT for {cache_key}")
                return json.loads(cached)
        except Exception as e:
            print(f"⚠️ Cache read error: {e}")
    
    # Cache miss - fetch from sources
    print(f"❌ Cache MISS for {cache_key}")
    
    # Filter sources by category if provided
    if category:
        sources = db. query(models.Source).filter(models.Source.category == category).all()
    else:
        sources = db.query(models. Source).all()
    
    all_items = []

    for src in sources:
        try:
            source = {"name":  src.name, "url": src.url, "feed_type":  src.feed_type}
            items = feeds.fetch_feed_for_source(source)
            # attach source name - take more items per source for better mixing
            for it in items[: 15]: 
                it.setdefault("source", src.name)
                all_items.append(it)
        except Exception: 
            # ignore failing sources to keep overall feed resilient
            continue

    # Sort ALL items together using the hot/new algorithm
    all_items = feeds.sort_items(all_items, sort)

    # Store in cache for 5 minutes
    if redis_client: 
        try:
            redis_client.setex(cache_key, 300, json.dumps(all_items))
            print(f"💾 Cached {cache_key}")
        except Exception as e:
            print(f"⚠️ Cache write error: {e}")
    
    return all_items

@app.api_route("/", methods=["GET", "HEAD"])
def read_root():
    return {"message": "Welcome to DevPulse API"}


# ============ FAVORITES ENDPOINTS ============

@app. get("/favorites", response_model=list[schemas. FavoriteResponse])
def get_favorites(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    """Get all favorites for the current user"""
    return db.query(models.Favorite).filter(
        models. Favorite.user_id == current_user.id
    ).order_by(models.Favorite. created_at.desc()).all()


@app.get("/favorites/links")
def get_favorite_links(
    current_user: models. User = Depends(auth.get_current_user),
    db: Session = Depends(database. get_db)
):
    """Get just the links of favorited items for quick lookup"""
    favorites = db. query(models.Favorite. feed_link).filter(
        models. Favorite.user_id == current_user.id
    ).all()
    return [f.feed_link for f in favorites]


@app.post("/favorites", response_model=schemas.FavoriteResponse)
def add_favorite(
    favorite: schemas.FavoriteCreate,
    current_user: models. User = Depends(auth.get_current_user),
    db: Session = Depends(database. get_db)
):
    """Add a feed item to favorites"""
    # Check if already favorited
    existing = db.query(models.Favorite).filter(
        models. Favorite.user_id == current_user.id,
        models. Favorite.feed_link == favorite.feed_link
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Already favorited")
    
    new_favorite = models.Favorite(
        user_id=current_user.id,
        feed_link=favorite.feed_link,
        feed_title=favorite.feed_title,
        feed_source=favorite.feed_source,
        feed_published=favorite.feed_published,
        feed_summary=favorite.feed_summary
    )
    db.add(new_favorite)
    db.commit()
    db.refresh(new_favorite)
    return new_favorite


@app.delete("/favorites")
def remove_favorite(
    feed_link: str,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    """Remove a feed item from favorites"""
    favorite = db.query(models. Favorite).filter(
        models. Favorite.user_id == current_user.id,
        models.Favorite.feed_link == feed_link
    ).first()
    
    if not favorite: 
        raise HTTPException(status_code=404, detail="Favorite not found")
    
    db.delete(favorite)
    db.commit()
    return {"message": "Favorite removed"}
