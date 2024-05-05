import requests
import re
import urllib.request
from bs4 import BeautifulSoup
from collections import deque
from html.parser import HTMLParser
from urllib.parse import urlparse
import os
import pdfCrawl
import threading
from queue import Queue
from seperate_words import separate_text_file
import tempfile
from scrape_and_embed_use_tmp import scrape_and_embed
import shutil
from concurrent.futures import ThreadPoolExecutor
def crawl_using_threads(url):#,tmp_dir):
    # Regex pattern to match a URL
    HTTP_URL_PATTERN = r'^http[s]{0,1}://.+$'

    # Create a class to parse the HTML and get the hyperlinks

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

    ################################################################################
    # Step 2
    ################################################################################

    # Function to get the hyperlinks from a URL

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

    ################################################################################
    # Step 3
    ################################################################################

    # Function to get the hyperlinks from a URL that are within the same domain

    def get_domain_hyperlinks(local_domain, url):
        clean_links = []
        for link in set(get_hyperlinks(url)):
            clean_link = None

            # If the link is a URL, check if it is within the same domain
            if re.search(HTTP_URL_PATTERN, link):
                # Parse the URL and check if the domain is the same
                url_obj = urlparse(link)
                if url_obj.netloc == local_domain:
                    clean_link = link

            # If the link is not a URL, check if it is a relative link
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

        # Return the list of hyperlinks that are within the same domain
        return list(set(clean_links))

    ################################################################################
    # Step 4
    ################################################################################
    def clean_text_files(folder_path, debug=False):
        for filename in os.listdir(folder_path):
            if filename.endswith('.txt'):
                file_path = os.path.join(folder_path, filename)
                separate_text_file(file_path)

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
    def is_valid_link(link):
        # Add more file extensions to this list if needed
        invalid_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.pdf']
        
        # Check if the link ends with a valid extension
        if any(link.endswith(ext) for ext in invalid_extensions):
            return False
        
        # Check if the link has a valid extension followed by a question mark or ampersand
        for ext in invalid_extensions:
            if f"{ext}?" in link or f"{ext}&" in link:
                return False
        
        return True
    
    def crawl_worker(url, local_domain, seen, queue):
        print(f"crawl {url}")
        try:
            for link in get_domain_hyperlinks(local_domain, url):
                if link not in seen:
                    queue.append(link)
                    seen.add(link)
        except:
            pass

    def crawl(url):
        local_domain = urlparse(url).netloc
        queue = deque([url])
        seen = {url}
        url_cnt = 0

        with ThreadPoolExecutor() as executor:
            while queue:
                url = queue.pop()
                while not is_valid_link(url):
                    print(f"the url {url} contain no data")
                    if queue: 
                        url = queue.pop()
                executor.submit(crawl_worker, url, local_domain, seen, queue)
                url_cnt += 1

        print(f"this is the amount of hyperlinks: {url_cnt}")
        return seen
 
        
    parsed_url = urlparse(url)
    local_domain = parsed_url.netloc
    seen = crawl(url)
    # Create a queue to store the URLs
    url_queue = Queue()
    for link in seen:
        url_queue.put(link)
    def scrape_data(tmp_dir, local_domain):
        while not url_queue.empty():
            # Get the next URL from the queue
            url = url_queue.get()
            target_path = os.path.join(tmp_dir, local_domain, f"{url[8:].replace('/', '_')}.txt")
            with tempfile.NamedTemporaryFile(mode='w+', suffix=".txt", dir=tmp_dir, delete=False, encoding="UTF-8") as tmp_file:
                try:
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}
                    if pdfCrawl.is_pdf_url(url):
                        pdfCrawl.download_pdf(url)
                        pdfCrawl.pdf_to_txt('tempPDF.pdf', tmp_file)
                        pdfCrawl.delete_file('tempPDF.pdf')
                    else:
                        soup = BeautifulSoup(requests.get(url, headers=headers).text, "html.parser")
                        text =target_path+"\n\n"+soup.get_text()
                        if "You need to enable JavaScript to run this app." in text:
                            print("Unable to parse page " + url + " due to JavaScript being required")
                        else:
                            tmp_file.write(text)

                    os.makedirs(os.path.dirname(target_path), exist_ok=True)
                    print(f"scraping data {target_path}")
                except Exception as e:
                    print(f"An error occurred while processing {url}: {e}")
                finally:
                # Mark the task as done in the queue
                    url_queue.task_done()
        

    def scrape_using_threads(tmp_dir,local_domain):
        # Define the number of threads you want to use
        num_threads = 500  # You can adjust this as needed

        # Create and start the threads
        threads = []
        for _ in range(num_threads):
            thread = threading.Thread(target=scrape_data(tmp_dir=tmp_dir,local_domain=local_domain))
            thread.start()
            threads.append(thread)

        # Wait for all threads to finish
        for thread in threads:
            thread.join()

        # All threads have finished, and the queue is empty
        print("Scraping is complete")

    def rename_files_in_directory(directory_path):
        url_cnt=0
        url_renamed_cnt=0
        for filename in os.listdir(directory_path):
            url_cnt+=1
            file_path = os.path.join(directory_path, filename)
            try:
                # Check if it's a file (not a subdirectory)
                if os.path.isfile(file_path):
                    # Open the file and read the first line
                    with open(file_path, 'r', encoding='UTF-8') as file:
                        first_line = file.readline().strip().split("\\")[-1]
                        if not first_line:
                            print(f"Empty first line in file: {file_path}")
                            continue
                        print(first_line)
                    
                    os.rename(file_path,os.path.join(directory_path, first_line))
                    url_renamed_cnt+=1
            except FileExistsError:
                        # Skip renamed file that already exists
                print(f"that will remove"+file_path)
                os.remove(file_path)
                url_cnt-=1
                continue
            except Exception as e:
                try:
                    print(f"that will remove"+file_path)
                    os.remove(file_path)
                    url_cnt-=1
                except Exception as e:
                    print(f"Error deleting file: {e}")
                continue
        print(f"this is the amount of renamed urls {url_renamed_cnt} and this is all the urls {url_cnt}")


    
    tmp_dir = os.path.join(tempfile.gettempdir(), f"{local_domain}")
    # Create the temporary directory
    os.makedirs(tmp_dir, exist_ok=True)   
    scrape_using_threads(tmp_dir, local_domain)
    print("cleaning the text")
    clean_text_files(tmp_dir)
    print("rename files")
    rename_files_in_directory(tmp_dir)
    scrape_and_embed(local_domain,tmp_dir)
    shutil.rmtree(tmp_dir,ignore_errors=True)
    ###############################################################################################################
####take off before production#####
#######display only###
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
def is_valid_url(url):
    return True
def crawl_website_streaming_display(url):
    response = requests.get(url)

    if response.status_code != 200:
        raise Exception(f"Error fetching website: {url}")

    soup = BeautifulSoup(response.content, 'html.parser')

    for anchor in soup.find_all('a', href=True):
        href = anchor['href']

        # Construct absolute URL using urljoin
        absolute_url = urljoin(url, href)

        # Check if the URL is valid and yield it
        if is_valid_url(absolute_url):
            yield absolute_url
    

