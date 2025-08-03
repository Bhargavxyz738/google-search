from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from googlesearch import search
import os
import time
import random
from urllib.parse import urlparse

app = Flask(__name__)
CORS(app)

API_KEY = os.getenv("SEARCH_API_KEY")

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/apis/search', methods=['POST'])
def create_search():
    client_api_key = request.headers.get("x-api-key")
    if client_api_key != API_KEY:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    query = data.get("query")
    if not query:
        return jsonify({"error": "Missing 'query' parameter"}), 400

    try:
        num_results = int(data.get("num_results", 10))
    except (ValueError, TypeError):
        return jsonify({"error": "'num_results' must be an integer"}), 400
        
    unique = bool(data.get("unique", False))
    safe = data.get("safe", "off")
    advanced = bool(data.get("advanced", False))
    start_time = time.monotonic()

    try:
        search_generator = search(
            query,
            num_results=num_results,
            safe=safe,
            advanced=advanced
        )

        if not advanced:
            results = [{"url": url, "title": None, "description": None} for url in search_generator]
            return jsonify({"results": results})

        items = []
        for result_obj in search_generator:
            if not result_obj.url:
                continue

            display_link = urlparse(result_obj.url).netloc

            item = {
                "kind": "customsearch#result",
                "title": result_obj.title,
                "htmlTitle": f"<b>{result_obj.title}</b>",
                "link": result_obj.url,
                "displayLink": display_link,
                "snippet": result_obj.description,
                "htmlSnippet": f"This is a sample snippet. The description is: <b>{result_obj.description}</b>", 
                "formattedUrl": result_obj.url,
                "htmlFormattedUrl": result_obj.url,
                "pagemap": {
                    "cse_thumbnail": [
                        {
                            "src": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcT_M-A8n58a22s3YX-1g_L-Lq-Yg_w-Z7kLg&s",
                            "width": "225",
                            "height": "225"
                        }
                    ],
                    "metatags": [
                        {
                            "og:title": result_obj.title,
                            "og:description": result_obj.description
                        }
                    ]
                }
            }
            items.append(item)

        search_time = time.monotonic() - start_time
        total_results_count = str(random.randint(25000, 150000))

        response_data = {
            "kind": "customsearch#search",
            "context": {
                "title": "Custom Search Engine"
            },
            "queries": {
                "request": [
                    {
                        "title": f"Search for {query}",
                        "totalResults": total_results_count,
                        "searchTerms": query,
                        "count": len(items),
                        "startIndex": 1,
                        "inputEncoding": "utf8",
                        "outputEncoding": "utf8",
                        "safe": safe,
                        "cx": "fake-cx-id-1234567890" 
                    }
                ],
                "nextPage": [
                    {
                        "title": f"Next page for {query}",
                        "totalResults": total_results_count,
                        "searchTerms": query,
                        "count": num_results,
                        "startIndex": 1 + num_results,
                        "inputEncoding": "utf8",
                        "outputEncoding": "utf8",
                        "safe": safe,
                        "cx": "fake-cx-id-1234567890"
                    }
                ]
            },
            "searchInformation": {
                "searchTime": search_time,
                "formattedSearchTime": f"{search_time:.2f}",
                "totalResults": total_results_count,
                "formattedTotalResults": f"{int(total_results_count):,}"
            },
            "items": items
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        app.logger.error(f"An error occurred during search: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":

    app.run(host='0.0.0.0', port=5000)
