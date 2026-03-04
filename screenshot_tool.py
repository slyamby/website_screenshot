import asyncio
import argparse
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright

async def capture_screenshot(url: str, width: int, height: int):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"screenshot_{timestamp}.png"
    output_path = Path.cwd() / filename

    print(f"\n Launching Browser...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": width, "height": height}
        )
        page = await context.new_page()

        print(f"Navigating to {url}...")
        await page.goto(url, wait_until="networkidle")

        print("Capturing full-page screenshot")
        await page.screenshot(path=str(output_path), full_page=True)

        await browser.close()

    print(f"\n Screenshot saved as: {output_path}")


def main():
    print("Script started...")
    parser = argparse.ArgumentParser(
        description="Capture a full-page screenshot of website."
    )

    parser.add_argument("url", help="Website URL (include https://)")
    parser.add_argument(
        "--width", type=int, default=1280, help="Viewport width (default: 1280)"
    )
    parser.add_argument(
        "--height", type=int, default=800, help="Viewport height (default: 800)" 
    )

    args = parser.parse_args()

    asyncio.run(capture_screenshot(args.url, args.width, args.height))


if __name__ == "__main__":
    main()
