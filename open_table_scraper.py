import asyncio
from playwright.async_api import async_playwright
import json
import playwright


async def scrape_opentable(metro_id: str, city_name: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        url = f"https://www.opentable.com/s?metroId={metro_id}"
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=120000)
        except playwright._impl._errors.TimeoutError:
            print(f"Timeout error when loading {url}. Retrying...")
            await page.goto(url, wait_until="domcontentloaded", timeout=180000)

        restaurants = []

        # Wait for the restaurant list to load
        await page.wait_for_selector('[data-testid="restaurant-cards"]')

        # Extract restaurant information
        restaurant_elements = await page.query_selector_all(
            ".multiSearchRestaurantCard"
        )

        for element in restaurant_elements:
            name = await element.query_selector(".FhfgYo4tTD0-")

            if name:
                name_text = await name.inner_text()
                restaurants.append({"name": name_text, "city": city_name})

        await browser.close()
        return restaurants


def import_metros():
    with open("./data/metros.json", "r") as file:
        data = json.load(file)

    metros = {}
    for metro in data["data"]["featuredMetrosListForDomain"]:
        city_name = metro["name"]
        metro_id = metro["metroId"]
        metros[city_name] = metro_id

    return metros


async def main():
    cities = import_metros()

    all_restaurants = []

    for city, metro_id in cities.items():
        print(f"Scraping restaurants in {city}...")
        try:
            restaurants = await scrape_opentable(metro_id=metro_id, city_name=city)
            all_restaurants.extend(restaurants)
        except Exception as e:
            print(f"Error scraping {city}: {str(e)}")
            continue

    # Save results to JSON
    with open("./data/opentable_restaurants.json", "w", encoding="utf-8") as jsonfile:
        json.dump(all_restaurants, jsonfile, ensure_ascii=False, indent=2)

    print(f"Scraped {len(all_restaurants)} restaurants in total.")


if __name__ == "__main__":
    asyncio.run(main())
