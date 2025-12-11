from fastapi import FastAPI, Query, Body
from fastapi.responses import JSONResponse
import random
import requests

app = FastAPI(title="Forsaken Wiki API")

# Preset data
QUOTES = [
    "Mrrp moew - jean degare fromage",
    "I've wet a guy's pants on here before so I think I'm worthy. - ozyull",
    "HI GUYS MY NAME IS MILDATAY AND IM A BIG BACK - info on mildatays account"
]

USER_QUOTES = []  # store user submitted quotes

FORSAKEN_WIKI_BASE = "https://forsaken2024.fandom.com/wiki/"

# --- GET endpoint ---
@app.get("/get")
def get_data(
    option: str = Query(..., description="Choose: image, multiple_images, quote, quote_author, random_page, latest_page, search, your_quotes"),
    author: str = Query(None, description="Author for quote_author option"),
    count: int = Query(1, description="Number of images for multiple_images"),
    query: str = Query(None, description="Search term for search option")
):
    # --- Your Quotes ---
    if option == "your_quotes":
        if USER_QUOTES:
            return JSONResponse({"type": "your_quotes", "quote": random.choice(USER_QUOTES)})
        return JSONResponse({"error": "No user quotes submitted yet."}, status_code=404)

    # --- Existing options ---
    elif option == "quote":
        selected_quote = random.choice(QUOTES)
        return JSONResponse({"type": "quote", "quote": selected_quote})

    elif option == "quote_author":
        if not author:
            return JSONResponse({"error": "Please provide an author."}, status_code=400)
        filtered = [q for q in QUOTES if author.lower() in q.lower()]
        if filtered:
            return JSONResponse({"type": "quote_author", "author": author, "quote": random.choice(filtered)})
        return JSONResponse({"error": f"No quotes found for author '{author}'."}, status_code=404)

    elif option == "random_page":
        url = "https://forsaken2024.fandom.com/api.php"
        params = {"action": "query", "list": "allpages", "format": "json", "aplimit": "50"}
        response = requests.get(url, params=params).json()
        pages = response.get("query", {}).get("allpages", [])
        if pages:
            page = random.choice(pages)
            page_url = f"{FORSAKEN_WIKI_BASE}{page['title'].replace(' ', '_')}"
            return JSONResponse({"type": "random_page", "title": page["title"], "url": page_url})
        return JSONResponse({"error": "No pages found."}, status_code=404)

    elif option == "latest_page":
        url = "https://forsaken2024.fandom.com/api.php"
        params = {"action": "query", "list": "recentchanges", "format": "json", "rclimit": 1, "rcprop": "title"}
        response = requests.get(url, params=params).json()
        changes = response.get("query", {}).get("recentchanges", [])
        if changes:
            page = changes[0]
            page_url = f"{FORSAKEN_WIKI_BASE}{page['title'].replace(' ', '_')}"
            return JSONResponse({"type": "latest_page", "title": page["title"], "url": page_url})
        return JSONResponse({"error": "No recent pages found."}, status_code=404)

    elif option == "search":
        if not query:
            return JSONResponse({"error": "Please provide a search query."}, status_code=400)
        url = "https://forsaken2024.fandom.com/api.php"
        params = {"action": "query", "list": "search", "srsearch": query, "format": "json", "srlimit": 10}
        response = requests.get(url, params=params).json()
        results = response.get("query", {}).get("search", [])
        if results:
            pages = [{"title": r["title"], "url": f"{FORSAKEN_WIKI_BASE}{r['title'].replace(' ', '_')}"} for r in results]
            return JSONResponse({"type": "search", "query": query, "results": pages})
        return JSONResponse({"error": f"No results found for '{query}'."}, status_code=404)

    elif option == "image":
        images = fetch_wiki_images()
        if images:
            return JSONResponse({"type": "image", "url": random.choice(images)})
        return JSONResponse({"error": "No images found."}, status_code=404)

    elif option == "multiple_images":
        images = fetch_wiki_images()
        if images:
            selected = random.sample(images, min(count, len(images)))
            return JSONResponse({"type": "multiple_images", "images": selected})
        return JSONResponse({"error": "No images found."}, status_code=404)

    else:
        return JSONResponse({"error": "Invalid option."}, status_code=400)


# --- POST endpoint to submit user quotes ---
@app.post("/submit_quote")
def submit_quote(quote: str = Body(..., description="Your quote text")):
    if quote.strip():
        USER_QUOTES.append(quote.strip())
        return JSONResponse({"status": "success", "message": "Quote submitted!", "quote": quote.strip()})
    return JSONResponse({"status": "error", "message": "Quote cannot be empty."}, status_code=400)


# --- Helper function to fetch images dynamically ---
def fetch_wiki_images(limit=50):
    url = "https://forsaken2024.fandom.com/api.php"
    params = {
        "action": "query",
        "generator": "allimages",
        "gailimit": str(limit),
        "prop": "imageinfo",
        "iiprop": "url",
        "format": "json"
    }
    response = requests.get(url, params=params).json()
    pages = response.get("query", {}).get("pages", {})
    image_urls = [img.get("imageinfo", [{}])[0].get("url") for img in pages.values()]
    return [url for url in image_urls if url]
