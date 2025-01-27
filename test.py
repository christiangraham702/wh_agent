# from langchain_community.document_loaders import WebBaseLoader

# loader = WebBaseLoader("https://www.whitehouse.gov/news/")

# docs = loader.load()

# print(docs)

import requests

response = requests.get("https://www.whitehouse.gov/news/")

print(response.text)