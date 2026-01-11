# 🚀 DevPulse - Developer News Aggregator

> A modern, real-time developer news aggregator that brings content from multiple sources into one beautiful interface.

![Tech Stack](https://img.shields.io/badge/Frontend-React%20%2B%20Vite-blue)
![Tech Stack](https://img.shields.io/badge/Backend-FastAPI%20%2B%20Python-green)
![Tech Stack](https://img.shields.io/badge/Database-SQLite%20%2B%20SQLAlchemy-orange)

---

## 📖 Table of Contents

- [What is DevPulse?](#what-is-devpulse)
- [High-Level Architecture](#high-level-architecture)
- [Features](#features)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Detailed Documentation](#detailed-documentation)
- [Tech Stack Explained](#tech-stack-explained)

---

## 🤔 What is DevPulse?

**DevPulse** is a web application that aggregates (collects) developer news from multiple sources like:

- 🟠 **Hacker News** - Tech news and discussions
- 🔥 **Reddit** - Customizable subreddits
- 🐙 **GitHub Trending** - Popular repositories
- 📦 **Product Hunt** - New tech products
- 📝 **DEV.to** - Developer articles
- And many more...

Instead of visiting 10+ websites daily, DevPulse brings everything to one place!

---

## 🏗️ High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER'S BROWSER                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     FRONTEND (React + Vite)                          │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐    │   │
│  │  │  Login   │  │ Sidebar  │  │ Feed List │  │ Search & Filters │    │   │
│  │  │  Page    │  │(Sources) │  │ (Items)   │  │                  │    │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ HTTP Requests (REST API)
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         BACKEND (FastAPI + Python)                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │    Auth     │  │   Feeds     │  │  Favorites  │  │   Sources   │        │
│  │  (JWT)      │  │  Fetcher    │  │   Manager   │  │   Config    │        │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    │                 │                 │
                    ▼                 ▼                 ▼
        ┌───────────────┐   ┌───────────────┐   ┌───────────────┐
        │   Database    │   │ External APIs │   │  RSS Feeds    │
        │   (SQLite)    │   │ (Reddit, HN)  │   │  (Scrapers)   │
        └───────────────┘   └───────────────┘   └───────────────┘
```

### How Data Flows (Simple Explanation)

1. **User opens the app** → Frontend loads in browser
2. **User logs in** → Frontend sends credentials to Backend
3. **Backend verifies** → Checks database, returns JWT token
4. **User views feeds** → Frontend requests data from Backend
5. **Backend fetches** → Gets data from various sources (APIs, RSS, scraping)
6. **Data returned** → Backend sends formatted data to Frontend
7. **UI updates** → Frontend displays the feed items

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔐 **Authentication** | Secure login/register with JWT tokens |
| 📰 **Multi-Source Feeds** | Aggregate from 10+ developer news sources |
| 🔍 **Search** | Filter feeds by keywords |
| ⭐ **Favorites** | Save articles to read later |
| 🔥 **Hot/New Sorting** | Sort by popularity or recency |
| 🎨 **Dark Themes** | Blue dark or pure black themes |
| 📱 **Responsive** | Works on desktop and mobile |
| 🔧 **Custom Reddit** | Choose your favorite subreddits |

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+** - Backend runtime
- **Node.js 18+** - Frontend runtime
- **npm** - Package manager

### Installation

```bash
# 1. Clone or navigate to the project
cd /path/to/agg2

# 2. Setup Backend
cd backend
pip install -r requirements.txt
python seeds.py  # Initialize database with sources
uvicorn main:app --reload  # Start backend server

# 3. Setup Frontend (new terminal)
cd frontend
npm install
npm run dev  # Start frontend server

# 4. Open in browser
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
```

### Environment Variables

Create a `.env` file in the root directory:

```env
# Reddit OAuth (optional, improves rate limits)
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret

# Product Hunt API (optional)
Product_hunt_API_Key=your_key
Product_hunt_API_Secret=your_secret

# JWT Secret (important for security!)
JWT_TOKEN_SECRET=your_random_secret_key
```

---

## 📁 Project Structure

```
agg2/
├── README.md              # You are here! (High-level overview)
├── docs/
│   ├── backend.md         # Backend architecture & details
│   ├── frontend.md        # Frontend architecture & details
│   ├── database.md        # Database schema & design
│   └── Future_work.md     # Future improvements
├── .env                   # Environment variables (secrets)
│
├── backend/               # Python FastAPI server
│   ├── main.py            # API endpoints
│   ├── auth.py            # Authentication logic
│   ├── feeds.py           # Feed fetching logic
│   ├── models.py          # Database models
│   ├── schemas.py         # API data schemas
│   ├── database.py        # Database connection
│   ├── seeds.py           # Initial data seeder
│   └── requirements.txt   # Python dependencies
│
└── frontend/              # React + Vite app
    ├── src/
    │   ├── App.jsx        # Main application
    │   ├── components/    # Reusable UI components
    │   ├── context/       # React Context (state)
    │   └── pages/         # Page components
    ├── package.json       # Node dependencies
    └── index.html         # Entry HTML
```

---

## 📚 Detailed Documentation

For deeper understanding, read these documents:

| Document | What You'll Learn |
|----------|-------------------|
| 📘 [Backend Architecture](docs/backend.md) | REST APIs, authentication, feed fetching, scraping |
| 📗 [Frontend Architecture](docs/frontend.md) | React components, state management, UI design |
| 📙 [Database Design](docs/database.md) | Tables, relationships, SQLAlchemy ORM |
| 📕 [Future Work](docs/Future_work.md) | Caching, Docker, deployment, improvements |

---

## 🛠️ Tech Stack Explained

### Why These Technologies?

| Technology | Why We Chose It |
|------------|-----------------|
| **FastAPI** | Fast, modern Python framework with automatic API docs |
| **SQLite** | Simple file-based database, no setup required |
| **SQLAlchemy** | Makes database operations easy with Python objects |
| **React** | Popular, component-based UI library |
| **Vite** | Super fast development server and bundler |
| **Tailwind CSS** | Utility-first CSS for rapid styling |
| **JWT** | Secure, stateless authentication tokens |

### For Beginners: What is...?

- **REST API**: A way for frontend and backend to communicate using HTTP requests (GET, POST, PUT, DELETE)
- **JWT (JSON Web Token)**: A secure token that proves you're logged in
- **ORM (Object-Relational Mapping)**: Lets you use Python objects instead of SQL queries
- **RSS Feed**: A standard format for websites to share their content
- **Web Scraping**: Extracting data from websites that don't have APIs

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## 📄 License

This project is open source and available under the MIT License.

---

<div align="center">

**Built with ❤️ for developers who want to stay updated**

</div>
