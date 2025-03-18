# 🎮 Game Emotion Analysis 

This project scrapes **Reddit, Twitter, YouTube, Steam, and Metacritic** for comments and reviews about different games.\
The collected data is used for **sentiment analysis, emotion detection, and trend analysis** before and after a game's release.

---

## 📌 **Setup Instructions**

### **1⃣ Install Dependencies**

Make sure you have **Python 3.7+** installed, then run:

```bash
pip install -r requirements.txt
```

---

### **2⃣ Configure API Keys**

This project requires API keys to access Reddit, Twitter, and YouTube data.\
To keep your keys secure, we use a `.env` file.

#### **How to Use **``**:**

1. **Copy the **``** file and rename it to **``:

   ```bash
   cp .env.example .env
   ```

   *(Windows users can manually create a copy and rename it to **`.env`**.)*

2. **Open the **``** file** and replace the placeholder values (`your_reddit_client_id`, `your_twitter_api_key`, etc.) with your actual API keys:

   ```ini
   # Reddit API
   REDDIT_CLIENT_ID=your_reddit_client_id
   REDDIT_CLIENT_SECRET=your_reddit_client_secret
   REDDIT_USER_AGENT=your_reddit_user_agent

   # Twitter API
   TWITTER_API_KEY=your_twitter_api_key
   TWITTER_API_SECRET=your_twitter_api_secret
   TWITTER_ACCESS_TOKEN=your_twitter_access_token
   TWITTER_ACCESS_SECRET=your_twitter_access_secret

   # YouTube API
   YOUTUBE_API_KEY=your_youtube_api_key

   # MongoDB Connection
   MONGO_ConnectionString=your_username:your_password@your_cluster.mongodb.net/?retryWrites=true&w=majority
   ```


3. **Save the **``** file** and you're good to go!

🚨 **Important:**

- Do **not** push your `.env` file to GitHub! (It’s already added to `.gitignore`.)
- The `.env.example` file **does not contain real API keys**—it’s just a template.

---

### **3⃣ Run the Scraper**

To start collecting data, run:

```bash
python your_script.py
```

The script will:

- ✅ **Validate API credentials** (skip if an API key is missing or invalid)
- ✅ **Scrape Reddit, Twitter, YouTube, Steam, and Metacritic** for game-related comments
- ✅ **Save all data as CSV files** in the `data/` folder

---

## 📂 **Collected Data Format**

Each platform saves its data as `data/{game}_{source}.csv`.\
Example for **Elden Ring**:

```
data/Elden Ring_reddit.csv
data/Elden Ring_twitter.csv
data/Elden Ring_youtube.csv
data/Elden Ring_steam.csv
data/Elden Ring_metacritic.csv
```

---

## 🛠 **Troubleshooting**

1. **Missing API Key?**

   - Ensure `.env` is correctly configured.
   - Run `print(os.getenv("YOUR_KEY"))` to check if Python can access the keys.

