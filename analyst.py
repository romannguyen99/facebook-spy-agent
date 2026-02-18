from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from config import Config
import json

class ContentAnalyzer:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash", 
            google_api_key=Config.GOOGLE_API_KEY,
            temperature=0.7
        )

    def analyze(self, posts_data, competitor_name):
        print(f"Sending {len(posts_data)} posts to Gemini for analysis...")

        # Convert list of dicts to a string for the prompt
        posts_str = json.dumps(posts_data, indent=2)

        template = """
        You are a Senior Social Media Strategist. I will provide you with a list of recent Facebook posts from a competitor named "{competitor_name}".
        
        Your goal is to spy on their strategy and report back with insights.

        Here is the raw data (Posts, Likes, Comments, Dates):
        {posts_data}

        Please generate a detailed report in Markdown format covering:
        1. Performance snapshot: Average likes/comments per post.
        2. Content pillars: What topics are they talking about most? (e.g., educational, promotional, memes).
        3. Top performing post: Which post got the most engagement? Show me its content
        4. Analyse the top performing post: Analyse why there are those indicators, what is the content about, 
        why the content written about that is effective? For example, a post about the quality of a school's canteen, 
        people are interested because of the current situation that there are many schools that are not transparent in students' eating, 
        which rival schools can post but they do not have a basis to prove such as the Ministry of Food Safety,...

        Write the report in English and Vietnamese and keep the tone professional but tactical.
        """

        prompt = PromptTemplate(
            input_variables=["competitor_name", "posts_data"],
            template=template
        )

        # Create the chain using the pipe operator |
        chain = prompt | self.llm
        
        # Invoke the chain
        response = chain.invoke({
            "competitor_name": competitor_name,
            "posts_data": posts_str
        })

        return response.content