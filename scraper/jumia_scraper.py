import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
}

def search_jumia(keyword, max_results=5):
    url = f"https://www.jumia.ci/catalog/?q={keyword}"
    response = requests.get(url, headers=HEADERS)

    print("Status code:", response.status_code)

    soup = BeautifulSoup(response.text, "lxml")

    products = soup.select("article.prd")
    print("Nombre de produits trouvés:", len(products))

    results = []
    for product in products[:max_results]:
        name_tag = product.select_one("h3.name")
        price_tag = product.select_one("div.prc")
        img_tag = product.select_one("img")
        link_tag = product.select_one("a.core")

        name = name_tag.get_text(strip=True) if name_tag else None
        price = price_tag.get_text(strip=True) if price_tag else None
        image = None
        if img_tag:
            image = img_tag.get("data-src") or img_tag.get("src")
        link = link_tag.get("href") if link_tag else None
        if link and link.startswith("/"):
            link = "https://www.jumia.ci" + link

        results.append({
            "name": name,
            "price": price,
            "image": image,
            "link": link
        })

    return results


if __name__ == "__main__":
    results = search_jumia("telephone")
    for r in results:
        print(r)
