import requests


BOOK_SEARCH_URL = "https://dapi.kakao.com/v3/search/book"


def search_books(query, kakao_api_key, size=10, target="title", sort="accuracy"):
    headers = {
        "Authorization": f"KakaoAK {kakao_api_key}"
    }

    params = {
        "query": query,
        "size": size,
        "target": target,
        "sort": sort
    }

    response = requests.get(BOOK_SEARCH_URL, headers=headers, params=params)
    response.raise_for_status()

    return response.json()
