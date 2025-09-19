# config.py
import os

class Config:
    MARKETS = ['Akron OH', 'Charlotte NC', 'Greensboro NC', 'Atlanta GA', 'Tampa FL']
    SCRAPE_SITES = ['redfin.com', 'homes.com', 'movoto.com']
    TIGER_URL = 'https://www.census.gov/cgi-bin/geo/shapefiles/index.php'
    PROXY_POOL = []  # vsc-ab later
    PINECONE_API_KEY = os.getenv('PINECONE_KEY')
    SQUARE_ACCESS_TOKEN = os.getenv('SQUARE_TOKEN')