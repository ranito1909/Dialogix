from html.parser import HTMLParser
import requests
import re
import urllib.request
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import os
import pdfCrawl
import threading
from queue import Queue

# Constants
HTTP_URL_PATTERN = r'^http[s]{0,1}://.+$'
COMMON_IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp')

# Configuration
NUM_THREADS = 125


# Function to check if a URL is an image URL
def is_image_url(url):
    try:
        response = requests.head(url, allow_redirects=False)
        final_url = response.url

        if urlparse(final_url).path.endswith(COMMON_IMAGE_EXTENSIONS):
            return True

        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', '').lower()
            if content_type.startswith('image/'):
                return True
    except Exception as e:
        print(f"Error checking image URL: {str(e)}")

    return False


class HyperlinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        # Create a list to store the hyperlinks
        self.hyperlinks = []

    # Override the HTMLParser's handle_starttag method to get the hyperlinks
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)

        # If the tag is an anchor tag, and it has a href attribute, add the href attribute to the list of hyperlinks
        if tag == "a" and "href" in attrs:
            self.hyperlinks.append(attrs["href"])


# Function to clean text files in a folder
def clean_text_files(folder_path, debug=False):
    for filename in os.listdir(folder_path):
        if filename.endswith('.txt'):
            file_path = os.path.join(folder_path, filename)

            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            if len(lines) == 0:
                if debug:
                    print(f"{filename} is empty, deleting file.")
                os.remove(file_path)
                continue

            cleaned_lines = []
            for line in lines:
                cleaned_line = line.strip()
                cleaned_line = re.sub('\s+', ' ', cleaned_line)

                if cleaned_line:
                    cleaned_lines.append(cleaned_line)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("\n".join(cleaned_lines))
                if debug:
                    print(f"{filename} cleaned.")


def get_hyperlinks(url):
    # Try to open the URL and read the HTML
    try:
        # Open the URL and read the HTML
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}
        request = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(request) as response:

            # If the response is not HTML, return an empty list
            if not response.info().get('Content-Type').startswith("text/html"):
                return []

            # Decode the HTML
            html = response.read().decode('utf-8')
    except Exception as e:
        print(e)
        return []

    # Create the HTML Parser and then Parse the HTML to get hyperlinks
    parser = HyperlinkParser()
    parser.feed(html)

    return parser.hyperlinks


# Function to scrape data from URLs
def scrape_data(url, local_domain):
    try:
        with open('text/' + local_domain + '/' + url[8:].replace("/", "_") + ".txt", "w", encoding="UTF-8") as f:
            if pdfCrawl.is_pdf_url(url):
                pdfCrawl.download_pdf(url)
                pdfCrawl.pdf_to_txt('tempPDF.pdf', f)
                pdfCrawl.delete_file('tempPDF.pdf')
            else:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
                }
                soup = BeautifulSoup(requests.get(url, headers=headers).text, "html.parser")
                text = soup.get_text()

                if "You need to enable JavaScript to run this app." in text:
                    print("Unable to parse page " + url + " due to JavaScript being required")
                else:
                    f.write(text)
    except Exception as e:
        print(f"Error scraping data from {url}: {str(e)}")


# Function to crawl and extract hyperlinks
def crawl(seed_url):
    local_domain = urlparse(seed_url).netloc
    queue = Queue()
    seen = set([seed_url])
    queue.put(seed_url)

    if not os.path.exists("text/"):
        os.mkdir("text/")

    if not os.path.exists(f"text/{local_domain}/"):
        os.mkdir(f"text/{local_domain}/")

    while not queue.empty():
        url = queue.get()
        print(url)
        try:
            for link in get_domain_hyperlinks(local_domain, url):
                if link not in seen:
                    queue.put(link)
                    seen.add(link)
        except Exception as e:
            print(f"Error crawling {url}: {str(e)}")
    return seen


# Function to get the hyperlinks from a URL that are within the same domain
def get_domain_hyperlinks(local_domain, url):
    clean_links = []
    for link in set(get_hyperlinks(url)):
        clean_link = None

        if re.search(HTTP_URL_PATTERN, link):
            url_obj = urlparse(link)
            if url_obj.netloc == local_domain:
                clean_link = link
        else:
            if link.startswith("/"):
                link = link[1:]
            elif (
                    link.startswith("#")
                    or link.startswith("mailto:")
                    or link.startswith("tel:")
            ):
                continue
            clean_link = "https://" + local_domain + "/" + link

        if clean_link is not None:
            if clean_link.endswith("/"):
                clean_link = clean_link[:-1]
            clean_links.append(clean_link)
    return list(set(clean_links))


# Main function for scraping a website
def scrape_website(seed_url):
    local_domain = urlparse(seed_url).netloc
    seen = crawl(seed_url)

    url_queue = Queue()
    for link in seen:
        url_queue.put(link)

    threads = []
    for _ in range(NUM_THREADS):
        thread = threading.Thread(target=scrape_data, args=(url_queue, local_domain))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

    print("Scraping is complete")

    clean_text_files(f'text/{local_domain}')


if __name__ == '__main__':
    seed_url = 'https://www.passportcard.co.il/'
    scrape_website(seed_url)