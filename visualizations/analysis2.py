# Import required libraries
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from textblob import TextBlob

# Load the dataset
df = pd.read_csv("processed_reviews_textblob.csv")

# Convert date and filter valid dates
df['commented_date'] = pd.to_datetime(df['commented_date'], errors='coerce')
df = df.dropna(subset=['commented_date'])

# Define aspect columns
aspect_columns = [
    "cost", "graphics", "platform", "storyline", "gameplay",
    "soundtrack", "difficulty", "collaboration", "performance", "replayability"
]

# --- Sentiment Distribution ---
sns.countplot(x="comment_sentiment", data=df)
plt.title("Comment Sentiment Distribution")
plt.show()

# --- Time Series Sentiment Trend ---
time_sentiment = df.groupby([df['commented_date'].dt.to_period('M'), 'comment_sentiment']).size().unstack(fill_value=0)
time_sentiment.index = time_sentiment.index.to_timestamp()
sns.lineplot(data=time_sentiment)
plt.title("Sentiment Over Time")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

# --- TextBlob Sentiment Recalculation ---
sample_df = df.sample(10000, random_state=42).copy()
sample_df['textblob_polarity'] = sample_df['comment'].apply(lambda x: TextBlob(str(x)).sentiment.polarity)
sample_df['textblob_sentiment'] = sample_df['textblob_polarity'].apply(lambda p: 'positive' if p > 0.1 else 'negative' if p < -0.1 else 'neutral')
pd.crosstab(sample_df['comment_sentiment'], sample_df['textblob_sentiment'])

# --- Aspect Sentiment Over Time ---
aspect_sentiments_long = df.melt(id_vars=["commented_date"], value_vars=aspect_columns, var_name="aspect", value_name="sentiment")
aspect_sentiments_long = aspect_sentiments_long[aspect_sentiments_long["sentiment"] != "none"].copy()
aspect_sentiments_long['month'] = aspect_sentiments_long['commented_date'].dt.to_period('M').dt.to_timestamp()
aspect_time_counts = aspect_sentiments_long.groupby(["month", "aspect", "sentiment"]).size().reset_index(name="count")

# --- Before vs After Analysis ---
before_df = df[df['commented'] == 'before']
after_df = df[df['commented'] == 'after']

def aspect_sentiment_counts(sub_df):
    sentiment_counts = {}
    for col in aspect_columns:
        sentiment_counts[col] = sub_df[col].value_counts()
    return pd.DataFrame(sentiment_counts).fillna(0)

before_counts = aspect_sentiment_counts(before_df)
after_counts = aspect_sentiment_counts(after_df)

# --- Genre-Level Aspect Sentiment ---
genre_sample_df = df.sample(50000, random_state=123)
genre_sample_df = genre_sample_df[genre_sample_df[aspect_columns].ne("none").any(axis=1)]
genre_aspect_sentiment = genre_sample_df.melt(id_vars=["genre"], value_vars=aspect_columns, var_name="aspect", value_name="sentiment")
genre_aspect_sentiment = genre_aspect_sentiment[genre_aspect_sentiment["sentiment"] != "none"]
genre_sentiment_counts = genre_aspect_sentiment.groupby(["genre", "aspect", "sentiment"]).size().reset_index(name="mention_count")

# --- Visualization by Genre and Aspect ---
top_genres = genre_sentiment_counts["genre"].value_counts().index[:5]
for genre in top_genres:
    genre_df = genre_sentiment_counts[genre_sentiment_counts["genre"] == genre]
    plt.figure(figsize=(12, 6))
    sns.barplot(data=genre_df, x="aspect", y="mention_count", hue="sentiment")
    plt.title(f"Aspect Sentiment Distribution for Genre: {genre}")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

# --- Specific Aspect Across Genres ---
def plot_aspect_sentiment_by_genre(aspect):
    aspect_data = genre_sentiment_counts[
        (genre_sentiment_counts["genre"].isin(top_genres)) &
        (genre_sentiment_counts["aspect"] == aspect)
        ]
    plt.figure(figsize=(10, 6))
    sns.barplot(data=aspect_data, x="genre", y="mention_count", hue="sentiment")
    plt.title(f"{aspect.capitalize()} Sentiment Across Top Genres")
    plt.tight_layout()
    plt.show()

for aspect in ["performance", "graphics", "storyline", "gameplay", "difficulty", "soundtrack", "collaboration", "cost"]:
    plot_aspect_sentiment_by_genre(aspect)

# --- Before vs After Release Visualization ---
before_after_sample = df.sample(50000, random_state=2025)
before_after_sample = before_after_sample[before_after_sample[aspect_columns].ne("none").any(axis=1)]
before_after_aspects = before_after_sample.melt(id_vars=["commented"], value_vars=aspect_columns, var_name="aspect", value_name="sentiment")
before_after_aspects = before_after_aspects[before_after_aspects["sentiment"] != "none"]
before_after_summary = before_after_aspects.groupby(["commented", "aspect", "sentiment"]).size().reset_index(name="mention_count")

# --- Overall Comparison Chart ---
plt.figure(figsize=(14, 8))
sns.barplot(data=before_after_summary, x="aspect", y="mention_count", hue="commented")
plt.title("Aspect Mentions Before vs After Release")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()
#%%
