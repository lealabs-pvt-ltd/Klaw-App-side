from .models import News
import requests
from django.utils import timezone
from datetime import timedelta

def extract_data():
    api_url = "http://15.206.169.204:8002/api/data"
    response = requests.get(api_url)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching data: {response.status_code}")
        return []

def update_news():
    # Check if the last update was more than 12 hours ago
    last_update = News.objects.first()  # Assuming there is at least one news item
    if last_update and timezone.now() - last_update.last_updated < timedelta(hours=12):
        return  # Skip update if last update was within the last 12 hours
    
    # Clear all existing news in the database
    News.objects.all().delete()

    # Fetch the latest news data from the API
    data = extract_data()
    
    if data:
        # Insert new data into the database (only top 10 news)
        for item in data[:10]:
            News.objects.create(
                title=item['TITLE'],
                date=item['DATE'],
                content=item['CONTENT'],
                last_updated=timezone.now()  # Set the current timestamp for each news item
            )