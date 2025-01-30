import praw
import tweepy
import requests
import json
from googleapiclient.discovery import build
from bs4 import BeautifulSoup
import pandas as pd
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import os
from dotenv import load_dotenv

# ========== 🎮 LIST OF GAMES BY GENRE ==========
games = {
    "RPG": ["Baldur's Gate 3", "Elden Ring"],
    "Shooter": ["Call of Duty: Modern Warfare III", "Overwatch 2"],
    "Survival": ["Palworld", "ARK: Survival Evolved"],
    "Open-World": ["GTA 6", "Cyberpunk 2077"],
    "Strategy": ["Age of Empires IV", "Total War: Warhammer III"]
}

# ========== 🔑 API CREDENTIALS ==========
load_dotenv()

# Load API credentials securely
REDDIT = {
    "client_id": os.getenv("REDDIT_CLIENT_ID"),
    "client_secret": os.getenv("REDDIT_CLIENT_SECRET"),
    "user_agent": os.getenv("REDDIT_USER_AGENT")
}

TWITTER = {
    "api_key": os.getenv("TWITTER_API_KEY"),
    "api_secret": os.getenv("TWITTER_API_SECRET"),
    "access_token": os.getenv("TWITTER_ACCESS_TOKEN"),
    "access_secret": os.getenv("TWITTER_ACCESS_SECRET")
}

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

# ========== ✅ API VALIDATION ==========
def is_valid_reddit():
    try:
        reddit = praw.Reddit(**REDDIT)
        reddit.user.me()  # Test authentication
        return True
    except Exception as e:
        print(f"❌ Reddit API error: {e}")
        return False

def is_valid_twitter():
    try:
        auth = tweepy.OAuthHandler(TWITTER["api_key"], TWITTER["api_secret"])
        auth.set_access_token(TWITTER["access_token"], TWITTER["access_secret"])
        api = tweepy.API(auth)
        api.verify_credentials()  # Test authentication
        return True
    except Exception as e:
        print(f"❌ Twitter API error: {e}")
        return False

def is_valid_youtube():
    try:
        youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
        youtube.search().list(q="test", part="snippet", maxResults=1).execute()  # Test query
        return True
    except Exception as e:
        print(f"❌ YouTube API error: {e}")
        return False

# **Check APIs ONCE before running**
USE_REDDIT = is_valid_reddit()
USE_TWITTER = is_valid_twitter()
USE_YOUTUBE = is_valid_youtube()

# ========== 🔍 SCRAPING FUNCTIONS ==========
def scrape_reddit(game):
    if not USE_REDDIT:
        print(f"⚠️ Skipping Reddit scraping for {game}, API disabled.")
        return

    try:
        reddit = praw.Reddit(**REDDIT)
        subreddit = reddit.subreddit("gaming")
        posts = subreddit.search(game, limit=50)

        comments_data = []
        for post in posts:
            post.comments.replace_more(limit=5)
            for comment in post.comments.list():
                comments_data.append([post.title, post.score, comment.body, comment.score])

        df = pd.DataFrame(comments_data, columns=["Post Title", "Post Score", "Comment", "Comment Score"])
        df.to_csv(f"data/{game}_reddit.csv", index=False)
        print(f"✅ Reddit data for {game} saved!")
    except Exception as e:
        print(f"❌ Error scraping Reddit for {game}: {e}")

def scrape_twitter(game):
    if not USE_TWITTER:
        print(f"⚠️ Skipping Twitter scraping for {game}, API disabled.")
        return

    try:
        auth = tweepy.OAuthHandler(TWITTER["api_key"], TWITTER["api_secret"])
        auth.set_access_token(TWITTER["access_token"], TWITTER["access_secret"])
        api = tweepy.API(auth)

        tweets = tweepy.Cursor(api.search_tweets, q=game, lang="en", tweet_mode="extended").items(50)
        tweet_data = [[tweet.user.screen_name, tweet.full_text, tweet.created_at, tweet.favorite_count, tweet.retweet_count] for tweet in tweets]

        df = pd.DataFrame(tweet_data, columns=["Username", "Tweet", "Date", "Likes", "Retweets"])
        df.to_csv(f"data/{game}_twitter.csv", index=False)
        print(f"✅ Twitter data for {game} saved!")
    except Exception as e:
        print(f"❌ Error scraping Twitter for {game}: {e}")

def scrape_youtube(game):
    if not USE_YOUTUBE:
        print(f"⚠️ Skipping YouTube scraping for {game}, API disabled.")
        return

    try:
        youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
        request = youtube.search().list(q=game, part="snippet", maxResults=1, type="video")
        response = request.execute()

        video_id = response["items"][0]["id"]["videoId"] if response["items"] else None
        if not video_id:
            print(f"⚠️ No YouTube video found for {game}")
            return

        request = youtube.commentThreads().list(part="snippet", videoId=video_id, textFormat="plainText", maxResults=50)
        response = request.execute()

        comments = [[item["snippet"]["topLevelComment"]["snippet"]["authorDisplayName"],
                     item["snippet"]["topLevelComment"]["snippet"]["textDisplay"],
                     item["snippet"]["topLevelComment"]["snippet"]["likeCount"]] for item in response["items"]]

        df = pd.DataFrame(comments, columns=["Author", "Comment", "Likes"])
        df.to_csv(f"data/{game}_youtube.csv", index=False)
        print(f"✅ YouTube data for {game} saved!")
    except Exception as e:
        print(f"❌ Error scraping YouTube for {game}: {e}")

def scrape_steam(game, app_id, num_reviews=500):
    url = f"https://store.steampowered.com/appreviews/{app_id}?json=1&num_per_page=100"

    all_reviews = []
    cursor = "*"  # Used for pagination

    while len(all_reviews) < num_reviews:
        response = requests.get(f"{url}&cursor={cursor}")
        data = response.json()

        if "reviews" not in data:
            break

        for review in data["reviews"]:
            all_reviews.append([
                review["review"],
                review["voted_up"],
                review["votes_up"],
                review["votes_funny"]
            ])

        if "cursor" in data and data["cursor"] != cursor:
            cursor = data["cursor"]
        else:
            break  # Stop if no more new reviews

    # Limit to requested number
    all_reviews = all_reviews[:num_reviews]

    df = pd.DataFrame(all_reviews, columns=["Review", "Positive", "Helpful Votes", "Funny Votes"])
    df.to_csv(f"data/{game}_steam.csv", index=False)
    print(f"✅ Steam reviews for {game} ({len(all_reviews)} total) saved!")





def scrape_metacritic(game):
    formatted_game = game.lower().replace(" ", "-")
    url = f"https://www.metacritic.com/game/pc/{formatted_game}/user-reviews"

    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.get(url)
        time.sleep(5)  # Wait for JavaScript content to load

        # Scroll down to load more reviews
        for _ in range(5):  # Scroll 5 times
            driver.find_element(By.TAG_NAME, "body").send_keys(Keys.END)
            time.sleep(2)

        # Click "Expand" buttons to reveal full reviews
        expand_buttons = driver.find_elements(By.CLASS_NAME, "expand_collapse")
        for btn in expand_buttons:
            try:
                driver.execute_script("arguments[0].click();", btn)
                time.sleep(1)
            except:
                pass

        # Extract reviews
        reviews = []
        review_elements = driver.find_elements(By.CSS_SELECTOR, ".review_content .blurb")
        for review in review_elements:
            reviews.append(review.text.strip())

        driver.quit()

        # Save to CSV if reviews exist
        if reviews:
            df = pd.DataFrame(reviews, columns=["Review"])
            df.to_csv(f"data/{game}_metacritic.csv", index=False)
            print(f"✅ Metacritic reviews for {game} saved!")
        else:
            print(f"⚠️ No Metacritic reviews found for {game}.")

    except Exception as e:
        print(f"❌ Error scraping Metacritic for {game}: {e}")
        driver.quit()
# ========== 🚀 RUNNING SCRAPER FOR EACH GAME ==========
def run_scraper():
    steam_ids = {
        "Baldur's Gate 3": "1086940",
        "Elden Ring": "1245620",
        "Call of Duty: Modern Warfare III": "2512980",
        "Overwatch 2": "2357570",
        "Palworld": "1623730",
        "ARK: Survival Evolved": "346110",
        "GTA 6": None,  # Not released yet
        "Cyberpunk 2077": "1091500",
        "Age of Empires IV": "1466860",
        "Total War: Warhammer III": "1142710"
    }

    for genre, game_list in games.items():
        for game in game_list:
            print(f"\n📌 Scraping data for: {game} ({genre})...") 
            scrape_reddit(game) 
            scrape_twitter(game) 
            scrape_youtube(game) 
            if steam_ids.get(game):
                scrape_steam(game, steam_ids[game])
            scrape_metacritic(game)
            time.sleep(5)  # Avoid rate limits

run_scraper()
