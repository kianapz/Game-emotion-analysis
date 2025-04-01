import pandas as pd
import re
from textblob import TextBlob

# Load your dataset
df = pd.read_csv("visualizations\processed_reviews_textblob.csv", parse_dates=["commented_date"])

# Define regex patterns for feature extraction
feature_patterns = {
    'multiplayer': r"\b(multiplayer|coop|co-op|cooperative)\b",
    'bugs': r"\b(bug|glitch|crash|broken|issue|lag|fix)\b",
    'graphics': r"\b(graphic|visual|animation|texture|frame|fps)\b",
    'story': r"\b(story|plot|narrative|dialogue|cutscene)\b",
    'controls': r"\b(control|keyboard|input|mouse|joystick|gamepad)\b",
    'ai': r"\b(ai|enemy intelligence|npc behavior|bot)\b",
    'updates': r"\b(patch|update|version|release|hotfix)\b",
    'price': r"\b(price|cost|expensive|cheap|worth|value)\b"
}

# Split into 10k-sized chunks
chunk_size = 10000
chunks = [df.iloc[i:i + chunk_size] for i in range(0, len(df), chunk_size)]

# Function to process a single chunk
def process_chunk(chunk):
    chunk['polarity'] = chunk['comment'].astype(str).apply(lambda x: TextBlob(x).sentiment.polarity)
    chunk['subjectivity'] = chunk['comment'].astype(str).apply(lambda x: TextBlob(x).sentiment.subjectivity)
    
    for feature, pattern in feature_patterns.items():
        chunk[f"{feature}_mentioned"] = chunk['comment'].astype(str).str.lower().apply(lambda x: bool(re.search(pattern, x)))
    
    return chunk

# Process all chunks
processed_chunks = []
for i, chunk in enumerate(chunks):
    print(f"Processing chunk {i+1}/{len(chunks)}...")
    processed_chunks.append(process_chunk(chunk))

# Merge all chunks into one DataFrame
processed_df = pd.concat(processed_chunks, ignore_index=True)

# Save the full enhanced dataset
processed_df.to_csv("enhanced_reviews_dataset.csv", index=False)
