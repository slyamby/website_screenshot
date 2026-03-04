import asyncio
import argparse
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright
from PIL import Image
import traceback
from urllib.parse import urlparse


async def capture_site(page, url, full_dir, thumb_dir):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    parsed = urlparse(url)
    safe_name = parsed.netloc.replace(".","_")
    filename = f"{safe_name}_{timestamp}.png"

    full_path = full_dir / filename
    thumb_path = thumb_dir / filename

    try:
        print(f"\n Processing: {url}")
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await page.screenshot(path=str(full_path), full_page=True)
        print("Full-size screenshot saved")

        # Create thumbnail
        with Image.open(full_path) as img:
            img.thumbnail((400, 300))
            img.save(thumb_path)
        print("Thumbnail created")

        return {"url": url, "status": "Success"}
    
    except Exception as e:
        print(f"Failed: {url}")
        return {"url": url, "Status": f"Failed - {str(e)}"}
    

async def process_urls(file_path):
    base_dir = Path.cwd() / "screenshots"
    full_dir = base_dir / "full"
    thumb_dir = base_dir / "thumbnails"

    full_dir.mkdir(parents=True, exist_ok=True)
    thumb_dir.mkdir(parents=True, exist_ok=True)

    with open(file_path, "r") as f:
        urls = [line.strip() for line in f if line.strip()]

    results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1280, "height": 800})
        page = await context.new_page()

        for index, url in enumerate(urls, start=1):
            print(f"\n [{index}/{len(urls)}]")
            result = await capture_site(page, url, full_dir, thumb_dir)
            results.append(result)

        await browser.close()

    return results

def generate_report(results):
    print("\n Summary Report")
    print("-" * 40)
    success_count = 0
    failure_count = 0

    for result in results:
        print(f"{result['url']} → {result['status']}")
        if result["status"] == "Success":
            success_count += 1
        else:
            failure_count += 1

    print("-" * 40)
    print(f"Successful: {success_count}")
    print(f"Failed: {failure_count}")


def main():
    parser = argparse.ArgumentParser(
        description="Batch website screenshot and thumbnail generation"
    )
    parser.add_argument("file", help="Path to text file containing URLs")

    args = parser.parse_args()

    results = asyncio.run(process_urls(args.file))
    generate_report(results)

if __name__ == "__main__":
    main()
