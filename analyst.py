from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
import pandas as pd
from config import Config
import json

class ContentAnalyzer:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash", 
            google_api_key=Config.GOOGLE_API_KEY,
            temperature=0.7
        )

    def _calculate_stats(self, posts_data):
        if not posts_data:
            return "No data", "No data", "[]"

        # 1. Load Data into Pandas
        df = pd.DataFrame(posts_data)
        
        # Ensure numeric columns are actually numbers
        cols = ['likes', 'comments', 'shares']
        for col in cols:
            # Force conversion to numeric, turning errors to 0
            df[col] = pd.to_numeric(df.get(col, 0), errors='coerce').fillna(0)

        total_posts = len(df)
        avg_likes = df['likes'].mean()
        avg_comments = df['comments'].mean()
        avg_shares = df['shares'].mean()

        stats_summary = f"""
        - **Total Posts Scanned:** {total_posts}
        - **Avg Likes:** {avg_likes:.1f}
        - **Avg Comments:** {avg_comments:.1f}
        - **Avg Shares:** {avg_shares:.1f}
        """

        if 'format' in df.columns:
            # Group by format and calculate mean
            format_stats = df.groupby('format')[cols].mean().round(1)
            # Count how many of each format
            format_counts = df['format'].value_counts()
            
            # Combine into one readable text block for the AI
            format_summary_list = []
            for fmt in format_stats.index:
                count = format_counts.get(fmt, 0)
                likes = format_stats.loc[fmt, 'likes']
                comments = format_stats.loc[fmt, 'comments']
                shares = format_stats.loc[fmt, 'shares']
                format_summary_list.append(f"| {fmt} | {count} posts | {likes} likes | {comments} comments | {shares} shares |")
            
            format_summary_str = "\n".join(format_summary_list)
        else:
            format_summary_str = "No format data available."

        # Calculate total engagement score
        df['engagement'] = df['likes'] + df['comments'] + df['shares']
        # Sort descending
        top_posts_df = df.sort_values(by='engagement', ascending=False).head(10)
        
        # Convert to list of dicts for the prompt
        top_posts_list = []
        for _, row in top_posts_df.iterrows():
            top_posts_list.append({
                "url": row.get('url', '#'),
                "text_snippet": row.get('text', '')[:150].replace('\n', ' ') + "...",
                "likes": int(row['likes']),
                "comments": int(row['comments']),
                "shares": int(row['shares']),
                "format": row.get('format', 'Unknown')
            })

        return stats_summary, format_summary_str, json.dumps(top_posts_list, indent=2)

    def analyze(self, posts_data, competitor_name):
        print(f"Calculating stats for {len(posts_data)} posts...")

        # Calculate stats and prepare text blocks for the prompt
        stats_str, format_stats_str, top_posts_str = self._calculate_stats(posts_data)
        
        # Prepare raw text for "Tone" analysis (JSON string)
        full_context_str = json.dumps(posts_data, indent=2)

        print("Sending pre-calculated data to Gemini for report generation...")

        # Craft the prompt with clear instructions and the pre-calculated stats
        template = """
        You are a Senior Social Media Strategist. I have scraped Facebook data for a competitor named "{competitor_name}".
        
        I have already performed the statistical calculations for you. 
        Your job is to interpret these numbers and the raw text to generate a strategic report.

        ### INPUT DATA:
        **A. General Statistics:**
        {stats_str}

        **B. Performance by Format (Averages):**
        {format_stats_str}

        **C. Top Performing Posts:**
        {top_posts_str}

        **D. Full Raw Data (Use this for Content/Topic/Tone analysis):**
        {full_context_str}

        ---

        ### REPORT OUTPUT (Markdown):
        Please generate 2 reports seperately in 2 languages (English and Vietnamese) with the following structure:

        ## 1. Page Overview
        - What is this page about?:
        - Content Strategy: What do they usually write?
        - Topics: List 3-5 recurring topics.
        - Goal/CTA: What are they trying to convince users to do?
        - Tone: Describe the voice (e.g., Professional, Humorous, Urgent).

        ## 2. Executive Summary
        - Brief summary of their winning strategy.
        - Key Finding: Which format is most engaged?

        ## 3. Overview of Posts
        - {stats_str}
        - *Review of statistics*: (Give a one-sentence verdict on these numbers).

        ## 4. Post Detail (Top performing posts)
        | Link | Content Summary (Short) | Likes | Comments | Shares | Format |
        |---|---|---|---|---|---|
        *(Fill this table using the 'Top Performing Posts' data provided above)*

        ## 5. Format Performance
        | Format | # Posts | Avg Likes | Avg Comments | Avg Shares | Conclusion |
        |---|---|---|---|---|---|
        *(Fill stats from 'Performance by Format' input. Add a short 'Conclusion' for each row).*

        ## 6. Analysis of Content & Topics
        - Analyze the text from the 'Full Raw Data'. 
        - What hooks are they using?
        - Are their captions long or short?
        - Do they use emojis heavily?

        ## 7. Insights & Conclusions
        - Summarize the correlation between Content + Format + Results.

        ## 8. Recommendation
        - Based on this competitor's data, what should I do? 
        - Give 3 specific actionable steps.
        """

        prompt = PromptTemplate(
            input_variables=["competitor_name", "stats_str", "format_stats_str", "top_posts_str", "full_context_str"],
            template=template
        )

        chain = prompt | self.llm
        
        response = chain.invoke({
            "competitor_name": competitor_name,
            "stats_str": stats_str,
            "format_stats_str": format_stats_str,
            "top_posts_str": top_posts_str,
            "full_context_str": full_context_str
        })

        return response.content