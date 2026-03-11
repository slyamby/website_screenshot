from fasthtml.common import *
from playwright.async_api import async_playwright
from PIL import Image
import asyncio
import os
import json
import zipfile

app, rt = fast_app()

SCREENSHOT_DIR = "screenshots"
THUMB_DIR = "thumbnails"
HISTORY_FILE = "history.json"

os.makedirs(SCREENSHOT_DIR, exist_ok=True)
os.makedirs(THUMB_DIR, exist_ok=True)

# Limit parallel browser pages
sem = asyncio.Semaphore(5)

# ----------------------
# Utility Functions
# ----------------------

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE) as f:
            return json.load(f)
    return []

def save_history(entry):
    history = load_history()
    history.insert(0, entry)

    with open(HISTORY_FILE, "w") as f:
        json.dump(history[:20], f)

def make_thumbnail(image_path, thumb_path):
    img = Image.open(image_path)
    img.thumbnail((300, 200))
    img.save(thumb_path)

def safe_name(url):
    return (
        url.replace("https://", "")
        .replace("http://", "")
        .replace("/", "_")
        .replace(":", "_")
    )

def normalize_url(url):
    if not url.startswith("http://") and not url.startswith("https://"):
        return "https://" + url
    return url

# ----------------------
# Screenshot Engine
# ----------------------

async def capture(browser, url):

    async with sem:

        page = await browser.new_page()

        try:
            print(f"Capturing {url}")

            await page.goto(url, timeout=60000)

            name = safe_name(url)

            screenshot = f"{SCREENSHOT_DIR}/{name}.png"
            thumb = f"{THUMB_DIR}/{name}.png"

            await page.screenshot(path=screenshot, full_page=True)

            make_thumbnail(screenshot, thumb)

            print(f"Saved screenshot: {screenshot}")

            return name

        except Exception as e:
            print(f"ERROR capturing {url}: {e}")
            return None

        finally:
            await page.close()

async def process_urls(urls):

    async with async_playwright() as p:

        browser = await p.chromium.launch()

        tasks = [capture(browser, url) for url in urls]

        results = await asyncio.gather(*tasks)

        await browser.close()

        return results

def create_zip(files):

    zip_path = "screenshots.zip"

    with zipfile.ZipFile(zip_path, "w") as z:

        for f in files:

            path = f"{SCREENSHOT_DIR}/{f}.png"

            if os.path.exists(path):
                z.write(path)

    return zip_path

# ----------------------
# UI Routes
# ----------------------

@rt("/")
def home():

    history = load_history()

    history_gallery = []

    for item in history:

        history_gallery.append(
            Div(
                Img(src=f"/thumbnails/{item}.png", width=200),
                Br(),
                A("Open", href=f"/screenshots/{item}.png", target="_blank")
            )
        )

    return Titled(
        "Website Screenshot Tool",

        Form(

            H3("Enter URLs"),

            Textarea(
                name="urls",
                rows=10,
                placeholder="Enter one URL per line"
            ),

            Br(),
            Button("Capture Screenshots"),

            method="post",
            action="/capture"
        ),

        Hr(),

        H3("Results"),
        Div(id="gallery"),

        Hr(),

        H3("Screenshot History"),
        Div(*history_gallery)
    )

@rt("/capture", methods=["POST"])
async def capture_route(urls: str = ""):

    if not urls:
        return Div("No URLs provided.")

    url_list = [
        normalize_url(u.strip())
        for u in urls.splitlines()
        if u.strip()
    ]

    files = [f for f in await process_urls(url_list) if f]

    if not files:
        return Div("No screenshots were captured. Check terminal logs.")

    for f in files:
        save_history(f)

    gallery = []

    for f in files:

        gallery.append(
            Div(

                Img(src=f"/thumbnails/{f}.png", width=300),

                Br(),

                A("Full Size", href=f"/screenshots/{f}.png", target="_blank"),

                " | ",

                A("Download", href=f"/screenshots/{f}.png", download=True),

                Hr()
            )
        )

    zip_file = create_zip(files)

    gallery.append(

        Div(
            H3("Download All Screenshots"),
            A("Download ZIP", href=f"/{zip_file}", download=True)
        )

    )

    return Div(*gallery)

serve()