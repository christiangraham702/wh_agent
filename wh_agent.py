import requests
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from bs4 import BeautifulSoup
import os

class NewsArticle(BaseModel):
    id: str
    title: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WhiteHouseAPI:
    BASE_URL = "https://www.whitehouse.gov/news"


    
    def fetch_articles(self) -> List[NewsArticle]:
        # Example fetch logic (replace with actual WhiteHouse.gov API or web scraping)
        links = self.get_article_links()

        articles = []
        for link in links:
            response = requests.get(link)
            soup = BeautifulSoup(response.text, 'html.parser')
            articles.append(soup)
        
        news_articles = []
        for article in articles:
            metas = article.find_all('meta')
            description = ""
            published_time = ""
            for meta in metas:
                if meta.get('name') == 'description':
                    description = meta.get('content')
                if meta.get('property') == 'article:published_time':
                    published_time = meta.get('content')
            
            # Generate unique ID using hash of title and time
            unique_id = str(hash(f"{article.title}{published_time}"))
            
            news_article = NewsArticle(
                id=unique_id,
                title=article.title.get_text(),
                content=article.text,
                metadata={
                    "description": description,
                    "published_time": published_time
                }
            )
            news_articles.append(news_article)
        return news_articles
        
    def get_article_links(self):
        # Read existing articles from file
        try:
            with open('data/read_articles.txt', 'r') as f:
                read_articles = set(f.read().splitlines())
        except FileNotFoundError:
            # Create directory if it doesn't exist
            os.makedirs('data', exist_ok=True)
            read_articles = set()
        
        # Get new articles
        response = requests.get(self.BASE_URL)
        soup = BeautifulSoup(response.text, 'html.parser')
        links = []
        new_articles = []
        
        for h2 in soup.find_all('h2'):
            link = h2.find('a').get('href')
            if link not in read_articles:
                links.append(link)
                new_articles.append(link)
        
        # Append new articles to the file
        if new_articles:
            with open('data/read_articles.txt', 'a') as f:
                for link in new_articles:
                    f.write(f"{link}\n")
        
        return links
    


if __name__ == "__main__":
    api = WhiteHouseAPI()
    articles = api.fetch_articles()
    print(articles)