import requests

def fetch_books(query="subject:classics"):
    url = f"https://openlibrary.org/search.json?q={query}&limit=12"
    headers = {
        "User-Agent": "MyBookApp/1.0 (contact@example.com)"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code != 200:
            return []
            
        data = response.json()
        books = []
        
        for item in data.get('docs', []):
            cover_id = item.get('cover_i')
            # Always construct HTTPS cover image links
            if cover_id:
                cover_url = f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"
            else:
                cover_url = "https://placehold.co/200x300/2a2d34/ffffff?text=No+Cover"
                
            authors = item.get('author_name', ['Unknown Author'])
            
            books.append({
                'title': item.get('title', 'Untitled'),
                'author': authors[0] if isinstance(authors, list) else authors,
                'year': item.get('first_publish_year', 'N/A'),
                'cover': cover_url,
                'cover_url': cover_url
            })
            
        return books
        
    except Exception as e:
        print(f"Error fetching from Open Library: {e}")
        return []