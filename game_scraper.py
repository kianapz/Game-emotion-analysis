import os
import time
import requests
import pandas as pd
import praw
import re
import tweepy
from googleapiclient.discovery import build
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv
from datetime import datetime, timezone

load_dotenv() # load keys

#########################################################
# VARIABLE DEFINITIONS
GAMES = {
    "RPG": {
        "Baldur's Gate 3": "1086940",
        "Elden Ring": "1245620",
        "Cyberpunk 2077": "1091500"
    },
    "Shooter": {
        "Call of Duty: Modern Warfare 3": "2512980",
        "Overwatch 2": "2357570"
    },
    "Survival": {
        "ARK: Survival Evolved": "346110",
        "Palworld": "1623730"
        
    },
    "Open-World": {
        "GTA 6": None,
        "Cyberpunk 2077": "1091500"
    },
    "Strategy": {
        "Age of Empires IV": "1466860",
        "Total War: Warhammer III": "1142710"
    },
    "Action": {
        "The Last of Us Part I": "1888930",
        "The Last of Us Part II": None,
        "Death Stranding": "1190460",
        "Red Dead Redemption 2": "1174180",
        "Detroit: Become Human": "1222140",
        "God of War Ragnarok": None 
    },
    "Adventure": {
        "Stray": "1332010",
        "Indiana Jones and the Great Circle": None
    },
    "Puzzle": {
        "Inside": "304430",
        "Limbo": "48000",
        "Little Nightmares": "424840",
        "It Takes Two": "1426210"
    }
}
REDDIT_CREDENTIALS = { # Get Reddit credentials
    "client_id": os.getenv("REDDIT_CLIENT_ID"),
    "client_secret": os.getenv("REDDIT_CLIENT_SECRET"),
    "user_agent": os.getenv("REDDIT_USER_AGENT")
}
TWITTER_CREDENTIALS = { # Get Twitter credentials
    "bearer_token": os.getenv("TWITTER_BEARER_TOKEN"),
    "username": os.getenv("TWITTER_USERNAME")
}
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")  # Get Youtube credential

#########################################################
# VALIDATION FUNCTIONS
def validate_reddit(): # Make sure reddit credential are valid
    try:
        reddit = praw.Reddit(**REDDIT_CREDENTIALS)
        reddit.user.me()
        return True
    except Exception as e:
        print(f"Reddit API error: {e}")
        return False
def validate_twitter(): # Make sure twitter credential are valid
    try:
        if not TWITTER_CREDENTIALS["bearer_token"]:
            raise ValueError("Missing Twitter Bearer Token!")
        client = tweepy.Client(bearer_token=TWITTER_CREDENTIALS["bearer_token"])
        response = client.get_user(username=TWITTER_CREDENTIALS["username"])  # Test authentication
        if response.data:
            return True
    except Exception as e: 
        print(f"Twitter API error: {e}")
        return False
def validate_youtube(): # Make sure youtube credential are valid
    try:
        youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
        youtube.search().list(q="test", part="snippet", maxResults=1).execute()
        return True
    except Exception as e:
        print(f"YouTube API error: {e}")
        return False

#########################################################
# SCRAPING FUNCTIONS
def scrape_reddit(game, directory):
    """
    Scrapes Reddit posts and comments related to a specific game.
    Args:
        game (str): The game name to search for.
        directory (str): The directory where the data will be saved.

    This function searches for Reddit posts related to the game, retrieves the comments, 
    and saves them to a CSV file containing the post title, post score, comment text, 
    and comment score.
    """
    try:
        reddit = praw.Reddit(**REDDIT_CREDENTIALS)
        subreddit = reddit.subreddit("gaming")
        posts = subreddit.search(game, limit=50)
        data = []
        for post in posts:
            post_date = datetime.fromtimestamp(post.created_utc, tz=timezone.utc).strftime('%Y-%m-%d')
            post.comments.replace_more(limit=10)  # Load top-level comments
            for comment in post.comments.list():
                if isinstance(comment, praw.models.MoreComments):  
                    continue  # Skip 'MoreComments' objects
                comment_date = datetime.fromtimestamp(comment.created_utc, tz=timezone.utc).strftime('%Y-%m-%d')
                data.append([post.id, post_date, comment_date, comment.body])
        # Save to CSV if data exists ( post.score, comment.score)
        if data:
            df = pd.DataFrame(data, columns=["Post ID", "Post Date",  "Comment Date", "Comment"])
            df.to_csv(f"{directory}/reddit_comments_{game}.csv", index=False)
            print(f"\tReddit data for {game} saved!")
        else:
            print(f"\tNo Reddit data for {game}.")
    except Exception as e:
        print(f"\tError scraping Reddit for {game}..: {e}")

def scrape_twitter(game, directory):
    """
    Scrapes Twitter for recent tweets related to a specific game.
    Args:
        game (str): The game name to search for.
        directory (str): The directory where the data will be saved.

    This function retrieves tweets containing the game name (excluding retweets), 
    and stores the tweet id, text, creation date, number of likes, and retweets in a CSV file.
    """
    try:
        client = tweepy.Client(bearer_token=TWITTER_CREDENTIALS["bearer_token"])  # Authenticate using the new Twitter API v2
        query = f"{game} -is:retweet lang:en" # no retweets & english comments
        tweets = client.search_recent_tweets(query=query, max_results=10, tweet_fields=["created_at", "public_metrics"])  # Max 10 to avoid hitting limits
        if not tweets.data:  # Check if tweets were retrieved
            print(f"\tNo recent tweets found for {game}.")
            return
        data = [  # Extract relevant data
            [
                tweet.id,
                tweet.text,
                tweet.created_at,
                tweet.public_metrics["like_count"],
                tweet.public_metrics["retweet_count"]
            ]
            for tweet in tweets.data
        ]
        if data:
            df = pd.DataFrame(data, columns=["Tweet ID", "Tweet", "Date", "Likes", "Retweets"])
            df.to_csv(f"{directory}/twitter_comments_{game}.csv", index=False) # Save to CSV
            print(f"\tTwitter data for {game} saved!")
        else: 
            print(f"\tNo Twitter data for {game}.")
    except Exception as e:
        print(f"\tError scraping Twitter for {game}: {e}")

def scrape_youtube(game, directory):
    """
    Scrapes YouTube for comments on videos related to a specific game.
    Args:
        game (str): The game name to search for.
        directory (str): The directory where the data will be saved.
    This function searches for YouTube videos related to the game, checks if comments are enabled, 
    and retrieves up to 25 comments per video. It saves the video title, video ID, 
    comment author, comment text, and like count in a CSV file.
    """
    try:
        youtube = build("youtube", "v3", developerKey=os.getenv("YOUTUBE_API_KEY"))
        search_request = youtube.search().list(
            q=game,
            part="snippet",
            maxResults=50, # Search for top 50 videos related to the game
            type="video"
        )
        search_response = search_request.execute()
        all_comments = []
        for item in search_response.get("items", []):
            video_id = item["id"].get("videoId")
            # video_title = item["snippet"]["title"]
            try: # Check if comments are enabled for this video
                comments_request = youtube.commentThreads().list(  
                    part="snippet",
                    videoId=video_id,
                    textFormat="plainText",
                    maxResults=1  # Just to check if comments are enabled
                ).execute()
            except Exception as e:
                if "commentsDisabled" in str(e):
                    continue  # Skip this video if comments are disabled
                else:
                    raise  
            
            comments = []
            next_page_token = None
            max_comment_count = 100
            while len(comments) < max_comment_count: # Fetch up to 50 comments for this video
                request = youtube.commentThreads().list(
                    part="snippet",
                    videoId=video_id,
                    textFormat="plainText",
                    maxResults=min(max_comment_count, max_comment_count - len(comments)),  # Fetch remaining comments
                    pageToken=next_page_token
                )
                response = request.execute()
                for item in response.get("items", []):
                    comment_data = item["snippet"]["topLevelComment"]["snippet"]
                    comments.append([
                        # video_title,
                        video_id,
                        comment_data["authorDisplayName"],
                        comment_data["publishedAt"],
                        comment_data["textDisplay"],
                        comment_data["likeCount"]
                    ])
                    if len(comments) >= max_comment_count:
                        break  # Stop when we have enough comments
                next_page_token = response.get("nextPageToken")
                if not next_page_token:
                    break  # No more pages left
            # Add to total comments list
            all_comments.extend(comments)
        # Save data if comments exist
        if all_comments:
            df = pd.DataFrame(all_comments, columns=["Video ID", "Author", "Date", "Comment", "Likes"])
            df.to_csv(f"{directory}/youtube_comments_{game}.csv", index=False)
            print(f"\tYoutube data for {game} saved!")
        else:
            print(f"\tNo Youtube data for {game}.")
    except Exception as e:
        print(f"\tError scraping YouTube for {game}: {e}")
    
def scrape_steam(game, directory, steamID):
    """
    Scrapes Steam reviews for a specific game.
    Args:
        game (str): The game name to scrape reviews for.
        directory (str): The directory where the data will be saved.
        steamID (str): The Steam App ID for the game.
    This function retrieves Steam reviews for the game using the Steam API, 
    and saves the review text, positivity, helpful votes, and funny votes in a CSV file.
    """
    if steamID is None: # Not released
        print(f"\tNo Steam data for {game}.")
        return 
    url = f"https://store.steampowered.com/appreviews/{steamID}?json=1&num_per_page=100"
    all_reviews = []
    cursor = "*"  # Used for pagination
    num_reviews=500
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
                review["votes_funny"],
                pd.to_datetime(review["timestamp_created"], unit='s')
            ])

        if "cursor" in data and data["cursor"] != cursor:
            cursor = data["cursor"]
        else:
            break  # Stop if no more new reviews
    # Limit to requested number
    all_reviews = all_reviews[:num_reviews]
    df = pd.DataFrame(all_reviews, columns=["Review", "Positive", "Helpful Votes", "Funny Votes" , "Date"])
    df.to_csv(f"{directory}/steam_comments_{game}.csv", index=False)
    print(f"\tSteam data for {game} saved!")

def scrape_metacritic(game, directory):
    """
    Scrapes Metacritic user reviews for a specific game.
    Args:
        game (str): The game name to search for on Metacritic.
        directory (str): The directory where the data will be saved.
    This function retrieves user reviews from Metacritic, including the username, score, 
    and review quote. It then saves the data to a CSV file.
    """
    gameName = re.sub(r"[',:]+", "", game.lower())
    gameName = gameName.replace(" ", "-")
    url = f"\thttps://www.metacritic.com/game/pc/{gameName}/user-reviews"
    # Set custom webdriver options
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    service = Service(ChromeDriverManager().install()) # Make sure correct webdriver is installed
    driver = webdriver.Chrome(service=service, options=options)
    driver.get(url) # get webpage
    time.sleep(2) # sleep to make sure webpage loads
    reviews = []
    try:
        review_blocks = driver.find_elements(By.CSS_SELECTOR, ".c-siteReview")
        # Loop through each review block and extract score, username, and quote
        for review in review_blocks:
            # Extract score
            score_element = review.find_element(By.CSS_SELECTOR, ".c-siteReviewScore span")
            score = score_element.text.strip() if score_element else "No Score"
            # Extract username
            username_element = review.find_element(By.CSS_SELECTOR, ".c-siteReviewHeader_username")
            username = username_element.text.strip() if username_element else "No Username"
            # Extract quote
            quote_element = review.find_element(By.CSS_SELECTOR, ".c-siteReview_quote span")
            quote = quote_element.text.strip() if quote_element else "No Quote"
            # Extract date
            date_element = review.find_element(By.CSS_SELECTOR, ".c-siteReviewHeader_reviewDate")
            date_obj = datetime.strptime(date_element.text.strip(), "%b %d, %Y")
            formatted_date = date_obj.strftime('%Y-%m-%d')
            reviews.append([
                username, 
                formatted_date,
                int(score) * 10,
                quote,
            ])
        driver.quit()
        # Save reviews to CSV if there are any
        if reviews:
            df = pd.DataFrame(reviews, columns=["Username", "Date", "Score %", "Review"])
            df.to_csv(f"{directory}/metacritic_comments_{game}.csv", index=False)
            print(f"\tMetacritic data for {game} saved!")
        else:
            print(f"\tNo Metacritic data for {game}.")
    except Exception as e:
        print(f"\tError scraping Metacritic for {game}: {e}")
        driver.quit()

#########################################################
# Run scrappers for each game
def run_scraper():
    """
    Loops through the list of games for each genre, 
    and calls scraping functions to gather data from various platforms (Reddit, Steam, etc.).

    This function initiates the scraping process for each game in `GAMES` by calling 
    individual scraping functions like `scrape_reddit`, `scrape_twitter`, etc.
    """
    for genre, game_list in GAMES.items():
        directory = f"./data/{genre}"
        os.makedirs(directory, exist_ok=True)
        for game, steamID in game_list.items():
            print(f"Scraping data for: {game} ({genre})...")
            # get reddit comments
            if validate_reddit(): 
                scrape_reddit(game, directory)
            # # get twitter comments (VERY LIMITED -> FIND FIX)
            # if validate_twitter(): 
            #     scrape_twitter(game, directory)
            # # get youtube comments
            if validate_youtube():
                scrape_youtube(game, directory)
            # # get steam comments
            scrape_steam(game, directory, steamID)
            # # # get metacritic comments
            scrape_metacritic(game, directory)
        time.sleep(5)  # Avoid rate limits 

def main():
    run_scraper() # run scrapper
    
if __name__ == "__main__":
    main()  