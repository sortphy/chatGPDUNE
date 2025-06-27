import os, requests, time, re
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from tqdm import tqdm
import json

class DuneWikiScraper:
    def __init__(self, base_url="https://dune.fandom.com", delay=1.0, max_pages=50):
        self.base_url = base_url
        self.delay = delay  # Be respectful to the server
        self.max_pages = max_pages
        self.scraped_urls = set()
        self.session = requests.Session()
        # Set a user agent to avoid being blocked
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; Educational RAG System)'
        })
    
    def clean_content(self, soup):
        """Remove unwanted elements and clean the content"""
        # Remove navigation, ads, and other non-content elements
        unwanted_selectors = [
            '.navbox', '.infobox', '.toc', '.mw-editsection',
            '.wikia-ad', '.fandom-sticky-header', '.page-header__actions',
            '.portable-infobox', '.references', '.reflist',
            'script', 'style', 'nav', 'footer'
        ]
        
        for selector in unwanted_selectors:
            for element in soup.select(selector):
                element.decompose()
        
        # Get the main content area
        content_selectors = [
            '.mw-parser-output',
            '.page-content',
            '#content',
            '.WikiaArticle'
        ]
        
        main_content = None
        for selector in content_selectors:
            main_content = soup.select_one(selector)
            if main_content:
                break
        
        if not main_content:
            # Fallback to body if no specific content area found
            main_content = soup.find('body')
        
        return main_content
    
    def extract_text_and_structure(self, soup):
        """Extract clean text while preserving some structure"""
        if not soup:
            return ""
        
        # Convert to text while preserving line breaks
        text = ""
        for element in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'div']):
            if element.name.startswith('h'):
                text += f"\n\n{element.get_text().strip()}\n"
                text += "=" * len(element.get_text().strip()) + "\n"
            else:
                element_text = element.get_text().strip()
                if element_text:
                    text += element_text + "\n"
        
        # Clean up excessive whitespace
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        
        return text.strip()
    
    def get_page_links(self, soup, base_url):
        """Extract relevant internal links from the page"""
        links = set()
        
        # Look for links in the main content
        for link in soup.find_all('a', href=True):
            href = link['href']
            
            # Convert relative URLs to absolute
            if href.startswith('/wiki/'):
                full_url = urljoin(base_url, href)
                
                # Only include Dune-related pages (basic filtering)
                if any(keyword in href.lower() for keyword in [
                    'dune', 'arrakis', 'atreides', 'harkonnen', 'spice',
                    'fremen', 'paul', 'leto', 'jessica', 'sandworm'
                ]):
                    links.add(full_url)
        
        return links
    
    def scrape_page(self, url):
        """Scrape a single page and return cleaned content"""
        try:
            print(f"Scraping: {url}")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Get page title
            title_elem = soup.find('h1') or soup.find('title')
            title = title_elem.get_text().strip() if title_elem else "Unknown Title"
            
            # Clean and extract content
            clean_soup = self.clean_content(soup)
            content = self.extract_text_and_structure(clean_soup)
            
            # Get internal links for further scraping
            links = self.get_page_links(soup, self.base_url)
            
            return {
                'url': url,
                'title': title,
                'content': content,
                'links': links
            }
            
        except Exception as e:
            print(f"Error scraping {url}: {e}")
            return None
    
    def scrape_wiki(self, start_urls, output_dir="./data/wiki"):
        """Scrape multiple pages starting from given URLs"""
        os.makedirs(output_dir, exist_ok=True)
        
        urls_to_scrape = set(start_urls)
        scraped_data = []
        
        print(f"Starting wiki scrape with {len(start_urls)} initial URLs")
        print(f"Maximum pages to scrape: {self.max_pages}")
        
        with tqdm(total=min(len(urls_to_scrape), self.max_pages), desc="Scraping pages") as pbar:
            while urls_to_scrape and len(scraped_data) < self.max_pages:
                url = urls_to_scrape.pop()
                
                if url in self.scraped_urls:
                    continue
                
                self.scraped_urls.add(url)
                
                # Scrape the page
                page_data = self.scrape_page(url)
                if page_data and page_data['content'].strip():
                    # Save as individual HTML file for your ingestion system
                    filename = self.url_to_filename(url)
                    filepath = os.path.join(output_dir, f"{filename}.html")
                    
                    # Create simple HTML structure
                    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>{page_data['title']}</title>
    <meta charset="utf-8">
</head>
<body>
    <h1>{page_data['title']}</h1>
    <div class="content">
        {self.text_to_html(page_data['content'])}
    </div>
    <meta name="source_url" content="{url}">
</body>
</html>"""
                    
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(html_content)
                    
                    scraped_data.append(page_data)
                    
                    # Add new links to scrape (limit to prevent infinite scraping)
                    if len(scraped_data) < self.max_pages:
                        new_links = page_data['links'] - self.scraped_urls
                        urls_to_scrape.update(list(new_links)[:5])  # Limit new links per page
                
                pbar.update(1)
                time.sleep(self.delay)  # Be respectful to the server
        
        # Save metadata
        metadata_file = os.path.join(output_dir, "scraping_metadata.json")
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump({
                'scraped_count': len(scraped_data),
                'urls_scraped': list(self.scraped_urls),
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }, f, indent=2)
        
        print(f"✓ Scraped {len(scraped_data)} pages")
        print(f"✓ Files saved to: {output_dir}")
        print(f"✓ Metadata saved to: {metadata_file}")
        
        return scraped_data
    
    def url_to_filename(self, url):
        """Convert URL to a safe filename"""
        # Extract the page name from the URL
        path = urlparse(url).path
        filename = path.split('/')[-1] or 'index'
        
        # Clean the filename
        filename = re.sub(r'[^\w\-_\.]', '_', filename)
        filename = re.sub(r'_+', '_', filename)
        filename = filename.strip('_')
        
        return filename or 'page'
    
    def text_to_html(self, text):
        """Convert plain text back to simple HTML structure"""
        lines = text.split('\n')
        html_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if it's a header (followed by ===)
            if line and len(lines) > lines.index(line) + 1:
                next_line = lines[lines.index(line) + 1] if lines.index(line) + 1 < len(lines) else ""
                if next_line.strip() and all(c == '=' for c in next_line.strip()):
                    html_lines.append(f"<h2>{line}</h2>")
                    continue
            
            # Skip the === lines
            if line and all(c == '=' for c in line):
                continue
            
            # Regular paragraph
            html_lines.append(f"<p>{line}</p>")
        
        return '\n'.join(html_lines)


# Example usage function to add to your main script
def scrape_dune_wiki():
    """Function to scrape Dune wiki content"""
    
    # Key Dune wiki pages to start with
    start_urls = [
        "https://dune.fandom.com/wiki/Dune",
        "https://dune.fandom.com/wiki/Paul_Atreides",
        "https://dune.fandom.com/wiki/Arrakis",
        "https://dune.fandom.com/wiki/Spice",
        "https://dune.fandom.com/wiki/House_Atreides",
        "https://dune.fandom.com/wiki/House_Harkonnen",
        "https://dune.fandom.com/wiki/Fremen",
        "https://dune.fandom.com/wiki/Sandworm",
        "https://dune.fandom.com/wiki/Duncan_Idaho",
        "https://dune.fandom.com/wiki/Leto_Atreides_I"
    ]
    
    scraper = DuneWikiScraper(
        delay=1.5,  # Be respectful - 1.5 seconds between requests
        max_pages=100  # Adjust based on your needs
    )
    
    # Create wiki subdirectory in your data folder
    wiki_dir = os.path.join("./data", "wiki")
    
    try:
        scraped_data = scraper.scrape_wiki(start_urls, wiki_dir)
        print(f"\n✅ Successfully scraped {len(scraped_data)} wiki pages")
        print(f"✅ HTML files saved to: {wiki_dir}")
        print("✅ Ready for ingestion with your existing system!")
        
        return wiki_dir
        
    except Exception as e:
        print(f"❌ Error during wiki scraping: {e}")
        return None


if __name__ == "__main__":
    scrape_dune_wiki()