import requests
import time
import gzip
import io
import os
import urllib3
import json
import argparse
import sys
import re

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def json_walkthroughs_to_markdown(src_dir, out_dir):
    """
    Converts all .json walkthroughs in src_dir to markdown files named after the first heading.
    """
    # Make out_dir if it doesn't exist
    os.makedirs(out_dir, exist_ok=True)

    # Loop through all files in src_dir
    for fname in os.listdir(src_dir):
        if not fname.endswith(".json"):
            continue
        fpath = os.path.join(src_dir, fname)
        with open(fpath, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except Exception as e:
                print(f"Skipping {fname}: {e}")
                continue

        instructions = data.get("data", {}).get("instructions", "")
        if not instructions:
            print(f"No instructions in {fname}")
            continue

        # Find the first markdown heading
        match = re.search(r"^#\s*(.+)", instructions, re.MULTILINE)
        if not match:
            print(f"No heading found in {fname}")
            continue
        heading = match.group(1).strip()
        # Clean filename: remove problematic chars, replace spaces with _
        safe_heading = re.sub(r"[^\w\s-]", "", heading)
        safe_heading = re.sub(r"\s+", "_", safe_heading)
        md_filename = f"{safe_heading}.md"
        md_path = os.path.join(out_dir, md_filename)

        # Optional: Clean up markdown (remove trailing whitespace, fix double newlines, etc.)
        cleaned = instructions.strip()
        cleaned = re.sub(r"\r\n", "\n", cleaned)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

        with open(md_path, "w", encoding="utf-8") as out:
            out.write(cleaned)
        print(f"Wrote {md_filename}")

def download_images_from_all_markdown(md_folder, image_dir):
    """
    Download images from all markdown files in md_folder to image_dir.
    """
    os.makedirs(image_dir, exist_ok=True)
    for fname in os.listdir(md_folder):
        if fname.endswith(".md"):
            md_path = os.path.join(md_folder, fname)
            print(f"Processing {md_path}")
            download_images(md_path, image_dir)

def download_images(md_path, image_root_dir, base_url="https://academy.hackthebox.com"):
    """
    Download images from markdown files, saving them in storage/walkthroughs/{number}/.
    """
    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()
    # Find all markdown image links
    image_urls = re.findall(r'!\[.*?\]\((.*?)\)', content)
    for url in image_urls:
        # Only handle relative URLs that start with /storage/walkthroughs/{number}/
        m = re.match(r"^/storage/walkthroughs/(\d+)/(.+)$", url)
        if m:
            number = m.group(1)
            filename = m.group(2)
            full_url = base_url.rstrip("/") + url
            # Save to image_root_dir/storage/walkthroughs/{number}/{filename}
            local_path = os.path.join(image_root_dir, "storage", "walkthroughs", number, filename)
        elif url.startswith("http://") or url.startswith("https://"):
            full_url = url
            filename = os.path.basename(url.split("?")[0])
            local_path = os.path.join(image_root_dir, filename)
        else:
            print(f"Skipping non-http(s) image: {url}")
            continue

        local_folder = os.path.dirname(local_path)
        os.makedirs(local_folder, exist_ok=True)

        if os.path.exists(local_path):
            print(f"Already downloaded: {local_path}")
            continue
        print(f"Downloading {full_url} -> {local_path}")
        try:
            resp = requests.get(full_url, stream=True)
            if resp.status_code == 200:
                with open(local_path, "wb") as img_file:
                    for chunk in resp.iter_content(1024):
                        img_file.write(chunk)
            else:
                print(f"Failed to download {full_url}: {resp.status_code}")
        except Exception as e:
            print(f"Error downloading {full_url}: {e}")
    
def fix_relative_image_links(md_folder):
    # All links in the markdown files that are '/storage/walkthroughs/{number}/{filename}' 
    # Should remove the / from the beginning of the image path
    for fname in os.listdir(md_folder):
        if fname.endswith(".md"):
            md_path = os.path.join(md_folder, fname)
            with open(md_path, "r", encoding="utf-8") as f:
                content = f.read()
            # Find all markdown image links
            image_urls = re.findall(r'!\[.*?\]\((.*?)\)', content)
            for url in image_urls:
                if url.startswith("/storage/walkthroughs/"):
                    new_url = url[1:]  # Remove the leading /
                    content = content.replace(url, new_url)
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(content)

def download_htb_academy_walkthroughs(base_url, download_dir, headers_path, cookies_path):
    """
    Download the JSON for all academy walkthroughs.
    """
    # Check for temp folder, if so skip
    if os.path.exists(download_dir):
        print(f"Warning: {download_dir} already exists. Skipping download.")
        return

    # Check for headers and cookies files
    if not os.path.isfile(headers_path):
        print(f"Error: headers file '{headers_path}' not found.")
        sys.exit(1)
    if not os.path.isfile(cookies_path):
        print(f"Error: cookies file '{cookies_path}' not found.")
        sys.exit(1)

    # Headers & Cookies
    with open(headers_path) as f:
        HEADERS = json.load(f)
    with open(cookies_path) as f:
        COOKIES = json.load(f)

    # Sanitize base_url: remove trailing slash if present
    base_url = base_url.rstrip('/')

    i = 1
    session = requests.Session()
    session.headers.update(HEADERS)
    session.cookies.update(COOKIES)

    while True:
        url = f"{base_url}/{i}"
        print(f"Fetching {url}")
        resp = session.get(url, verify=False)
        if resp.status_code == 404 and i > 250:
            print("No more walkthroughs available, leaving.")
            break
        elif resp.status_code != 200:
            print(f"Error fetching {url}: {resp.status_code}")
            i += 1
            continue
        elif resp.status_code == 200:
            print(f"Successfully fetched {url}")
            content = resp.content
            if not os.path.exists(download_dir):
                os.makedirs(download_dir)
            with open(os.path.join(download_dir, f"{i}.json"), "wb") as f:
                f.write(content)
            i += 1

if __name__ == "__main__":
    # Argument parser
    parser = argparse.ArgumentParser(description="Download Hack the Box (HTB) Academy walkthroughs.")
    parser.add_argument(
        "url",
        help="Base URL for walkthroughs, e.g. https://hackthebox.com/api/v1/product/labs/../channels/../modules/../walkthroughs/{}"
    )
    parser.add_argument(
        "--folder",
        default="./temp/",
        help="Folder for JSON files (default: ./temp/)"
    )
    parser.add_argument(
        "--headers",
        default="headers.json",
        help="Path to headers JSON file (default: headers.json)"
    )
    parser.add_argument(
        "--cookies",
        default="cookies.json",
        help="Path to cookies JSON file (default: cookies.json)"
    )
    # Parse arguments
    args = parser.parse_args()
    # Download walkthroughs
    download_htb_academy_walkthroughs(args.url, args.folder, args.headers, args.cookies)
    # Convert JSON to markdown
    json_walkthroughs_to_markdown("./temp", "./output")
    # Download images from markdown files
    download_images_from_all_markdown("./output", "./output")
    # Fix relative image links in markdown files for Obsidian
    fix_relative_image_links("./output")
    print("All done!")
