import os
import pandas as pd
import re
from datetime import datetime
from textblob import TextBlob
from langdetect import detect, DetectorFactory

DetectorFactory.seed = 0  # Ensure consistent language detection

# Define game release dates
RELEASE_DATES = {
    "Baldur's Gate 3": "2023-08-03",
    "Elden Ring": "2022-02-25",
    "Cyberpunk 2077": "2020-12-10",
    "Call of Duty: Modern Warfare 3": "2023-11-10",
    "Overwatch 2": "2022-10-04",
    "ARK: Survival Evolved": "2017-08-29",
    "Palworld": "2024-01-19",
    "Age of Empires IV": "2021-10-28",
    "Total War: Warhammer III": "2022-02-17",
    "The Last of Us Part I": "2022-09-02",
    "The Last of Us Part II": "2020-06-19",
    "Death Stranding": "2019-11-08",
    "Red Dead Redemption 2": "2018-10-26",
    "Detroit: Become Human": "2018-05-25",
    "God of War Ragnarok": "2022-11-09",
    "Stray": "2022-07-19",
    "Inside": "2016-06-29",
    "Limbo": "2010-07-21",
    "Little Nightmares": "2017-04-28",
    "It Takes Two": "2021-03-26"
}
# Invalid comment types present in dataset
INVALID_PATTERNS = [
    "spoiler alert this review contains spoilers.",
    "deleted",
    "removed"
]

def is_valid_comment(comment):
    """Remove invalid comments."""
    if pd.isna(comment) or not isinstance(comment, str):
        return False  # Empty or non-string values
    if any(pattern in comment.lower() for pattern in INVALID_PATTERNS):
        return False  # Contains invalid patterns
    if not re.match(r'^[A-Za-z]', comment.strip()):
        return False  # Does not start with a letter
    if not is_english(comment):
        return False  # Not in English
    return True

def is_english(comment):
    """Detects if the comment is in English."""
    return detect(comment) == 'en'

def process_csv(file_path, all_data):
    """Process a single CSV file by filtering and adding the "commented" and sentiment columns."""
    try:
        df = pd.read_csv(file_path)
        # Ensure required columns exist
        if not {'genre', 'game', 'commented_date', 'comment'}.issubset(df.columns):
            print(f"Skipping {file_path}: Missing required columns.")
            return
        # Filter comments
        df = df[df['comment'].apply(is_valid_comment)]
        # Convert comment column to string
        df['comment'] = df['comment'].astype(str)
        # Add 'commented' column
        if 'commented_date' in df.columns and 'game' in df.columns:
            df['commented'] = df.apply(lambda row: calculate_days_since_release(row['game'], row['commented_date']), axis=1)
        # Add 'comment_sentiment' column (renamed from 'polarity')
        df['comment_sentiment'] = df['comment'].apply(calculate_sentiment)
        # Append to all_data
        all_data.append(df)
    except Exception as e: # In case csv somehow doesn't have columns
        print(f"Error processing {file_path}: {e}")

def calculate_days_since_release(game, commented_date):
    """Determine if the comment was made before or after the game's release."""
    release_date_str = RELEASE_DATES.get(game)
    release_date = datetime.strptime(release_date_str, "%Y-%m-%d")
    comment_date = datetime.strptime(commented_date, "%Y-%m-%d")
    return "before" if comment_date < release_date else "after"

def calculate_sentiment(comment):
    """Calculate the sentiment of a comment using NLP."""
    sentiment = TextBlob(comment).sentiment.polarity
    if sentiment > 0:
        return "positive"
    elif sentiment < 0:
        return "negative"
    else:
        return "neutral"
    
def main():
    """Iterate through each CSV file in subfolders and process them."""
    data_dir = "../data"  # Root data folder
    all_data = []
    for genre_folder in os.listdir(data_dir):
        genre_path = os.path.join(data_dir, genre_folder)
        
        if os.path.isdir(genre_path):
            for file in os.listdir(genre_path):
                if file.endswith(".csv"):
                    file_path = os.path.join(genre_path, file)
                    process_csv(file_path, all_data)
    
    # Combine all datasets
    final_df = pd.concat(all_data, ignore_index=True)
    
    # Remove duplicate rows based on 'comment' column (or other unique identifiers)
    final_df = final_df.drop_duplicates(subset=['comment'], keep='first')
    
    # Reduce "after" comments by half, keeping longer ones
    after_df = final_df[final_df['commented'] == 'after']
    after_df = after_df.sort_values(by='comment', key=lambda x: x.str.len(), ascending=False)
    after_df = after_df.iloc[:len(after_df) // 2]
    
    # Combine back "before" and reduced "after" comments
    final_df = pd.concat([final_df[final_df['commented'] == 'before'], after_df], ignore_index=True)
    
    # Save the final dataset with 'comment_sentiment' and no duplicates
    final_df.to_csv("../data/final_comment_dataset.csv", index=False)
    
    print("Dataset saved as 'data/final_comment_dataset.csv'")

if __name__ == "__main__":
    main()