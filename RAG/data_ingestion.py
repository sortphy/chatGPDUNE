import os, subprocess, time, shutil, requests, atexit, re, json
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Neo4jVector
from langchain_community.document_loaders import TextLoader, PyPDFLoader, UnstructuredHTMLLoader, UnstructuredMarkdownLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from neo4j import GraphDatabase
from tqdm import tqdm
from dotenv import load_dotenv


# Load .env file variables
load_dotenv()


# Configuration
NEO4J_URI      = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
OLLAMA_URL     = os.getenv("OLLAMA_HOST", "http://localhost:11434")
EMBED_MODEL    = "nomic-embed-text"

# Tweakable settings
CHUNK_SIZE = 512          # Size of each text chunk
CHUNK_OVERLAP = 20        # Overlap between chunks
BATCH_SIZE = 200          # How many chunks to process at once
PROCESSING_TIMEOUT = 30   # Ollama startup timeout
DATA_DIR = "./data"       # Where your files are
INDEX_NAME = "dune_chunks" # Neo4j index name
NODE_LABEL = "DuneChunk"  # Neo4j node label

# Supported file extensions
SUPPORTED_EXTENSIONS = ['.txt', '.pdf', '.html', '.htm', '.md', '.markdown']


class DuneWikiScraper:
    def __init__(self, base_url="https://dune.fandom.com", delay=1.5, max_pages=50):
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
            'script', 'style', 'nav', 'footer', '.categories'
        ]
        
        for selector in unwanted_selectors:
            for element in soup.select(selector):
                element.decompose()
        
        # Get the main content area
        content_selectors = [
            '.mw-parser-output',
            '.page-content',
            '#content',
            '.WikiaArticle',
            '.main-content'
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
                    'fremen', 'paul', 'leto', 'jessica', 'sandworm', 'imperium',
                    'bene_gesserit', 'guild', 'mentat', 'kwisatz', 'stillsuit'
                ]) and not any(skip in href.lower() for skip in [
                    'category:', 'file:', 'template:', 'user:', 'talk:'
                ]):
                    links.add(full_url)
        
        return links
    
    def scrape_page(self, url):
        """Scrape a single page and return cleaned content"""
        try:
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
    <meta name="source_url" content="{url}">
</head>
<body>
    <h1>{page_data['title']}</h1>
    <div class="content">
        {self.text_to_html(page_data['content'])}
    </div>
</body>
</html>"""
                    
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(html_content)
                    
                    scraped_data.append(page_data)
                    
                    # Add new links to scrape (limit to prevent infinite scraping)
                    if len(scraped_data) < self.max_pages:
                        new_links = page_data['links'] - self.scraped_urls
                        urls_to_scrape.update(list(new_links)[:3])  # Limit new links per page
                
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
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Check if it's a header (followed by ===)
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if next_line and all(c == '=' for c in next_line):
                    html_lines.append(f"<h2>{line}</h2>")
                    continue
            
            # Skip the === lines
            if line and all(c == '=' for c in line):
                continue
            
            # Regular paragraph
            html_lines.append(f"<p>{line}</p>")
        
        return '\n'.join(html_lines)


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
        "https://dune.fandom.com/wiki/Leto_Atreides_I",
        "https://dune.fandom.com/wiki/Baron_Vladimir_Harkonnen",
        "https://dune.fandom.com/wiki/Bene_Gesserit",
        "https://dune.fandom.com/wiki/Spacing_Guild",
        "https://dune.fandom.com/wiki/Mentat",
        "https://dune.fandom.com/wiki/Kwisatz_Haderach"
    ]
    
    scraper = DuneWikiScraper(
        delay=1.5,  # Be respectful - 1.5 seconds between requests
        max_pages=75  # Reasonable limit for initial scraping
    )
    
    # Create wiki subdirectory in your data folder
    wiki_dir = os.path.join(DATA_DIR, "wiki")
    
    try:
        scraped_data = scraper.scrape_wiki(start_urls, wiki_dir)
        print(f"\n✅ Successfully scraped {len(scraped_data)} wiki pages")
        print(f"✅ HTML files saved to: {wiki_dir}")
        print("✅ Ready for ingestion with your existing system!")
        
        return wiki_dir
        
    except Exception as e:
        print(f"❌ Error during wiki scraping: {e}")
        return None


def ensure_ollama(model=EMBED_MODEL, timeout=PROCESSING_TIMEOUT):
    if not shutil.which("ollama"):
        raise RuntimeError("`ollama` binary not found in PATH.")

    # 1) Is the server already up?
    try:
        requests.get(f"{OLLAMA_URL}/api/tags", timeout=2)
        return                  # It's running – nothing to do.
    except requests.exceptions.RequestException:
        pass

    # 2) Start server in background (silent).
    proc = subprocess.Popen(
        ["ollama", "serve"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    atexit.register(proc.terminate)       # Kill it on script exit.

    # 3) Wait until the API answers.
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            requests.get(f"{OLLAMA_URL}/api/tags", timeout=1)
            break
        except requests.exceptions.RequestException:
            time.sleep(0.5)
    else:
        raise RuntimeError("Ollama server did not start in time.")

    # 4) Make sure the model is downloaded.
    subprocess.run(["ollama", "pull", model], check=True)


def clear_neo4j_database():
    """Clear existing chunks from Neo4j database"""
    print("Clearing existing data from Neo4j...")
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        with driver.session() as session:
            result = session.run(f"MATCH (n:{NODE_LABEL}) RETURN count(n) as count")
            count = result.single()["count"]
            if count > 0:
                session.run(f"MATCH (n:{NODE_LABEL}) DETACH DELETE n")
                print(f"✓ Cleared {count} existing chunks from database")
            else:
                print("✓ Database was already empty")
    except Exception as e:
        print(f"⚠ Warning: Could not clear database: {e}")
    finally:
        driver.close()


def get_appropriate_loader(file_path):
    """Return the appropriate LangChain loader for the file type"""
    _, ext = os.path.splitext(file_path.lower())
    
    if ext == '.pdf':
        return PyPDFLoader(file_path)
    elif ext in ['.html', '.htm']:
        return UnstructuredHTMLLoader(file_path)
    elif ext in ['.md', '.markdown']:
        return UnstructuredMarkdownLoader(file_path)
    elif ext == '.txt':
        # Try different encodings for text files
        for encoding in ['utf-8', 'latin-1', 'cp1252']:
            try:
                return TextLoader(file_path, encoding=encoding)
            except UnicodeDecodeError:
                continue
        # If all encodings fail, try with autodetect
        return TextLoader(file_path, autodetect_encoding=True)
    else:
        raise ValueError(f"Unsupported file extension: {ext}")


def load_and_chunk_documents(data_dir=DATA_DIR):
    """Load and chunk documents from various file formats"""
    docs = []
    
    # Get all supported files recursively (including subdirectories)
    supported_files = []
    
    for root, dirs, files in os.walk(data_dir):
        for fn in files:
            _, ext = os.path.splitext(fn.lower())
            if ext in SUPPORTED_EXTENSIONS:
                file_path = os.path.join(root, fn)
                relative_path = os.path.relpath(file_path, data_dir)
                supported_files.append((file_path, relative_path))
    
    if not supported_files:
        print(f"⚠ No supported files found in {data_dir}")
        print(f"Supported extensions: {', '.join(SUPPORTED_EXTENSIONS)}")
        return []
    
    print(f"Loading and chunking documents from {data_dir}...")
    print(f"Found {len(supported_files)} supported files (including subdirectories)")
    
    for file_path, relative_path in tqdm(supported_files, desc="Loading files"):
        _, ext = os.path.splitext(relative_path.lower())
        
        try:
            loader = get_appropriate_loader(file_path)
            file_docs = loader.load()
            
            # Add metadata about the source file and type
            for doc in file_docs:
                doc.metadata['source_file'] = relative_path
                doc.metadata['file_type'] = ext
                doc.metadata['file_path'] = file_path
                
                # Add wiki metadata if it's from wiki directory
                if 'wiki' in relative_path:
                    doc.metadata['source_type'] = 'wiki'
            
            docs.extend(file_docs)
            tqdm.write(f"✓ Loaded {relative_path} ({ext.upper()}) - {len(file_docs)} document(s)")
            
        except Exception as e:
            tqdm.write(f"✗ Failed to load {relative_path}: {e}")
            continue
    
    if not docs:
        raise RuntimeError("No documents were successfully loaded!")
    
    print(f"Splitting {len(docs)} documents into chunks...")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE, 
        chunk_overlap=CHUNK_OVERLAP
    )
    chunks = splitter.split_documents(docs)
    print(f"✓ Created {len(chunks)} chunks (chunk_size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")
    return chunks


def populate_neo4j_with_chunks(chunks):
    ensure_ollama()
    embeddings = OllamaEmbeddings(model=EMBED_MODEL)
    
    print(f"Generating embeddings and storing {len(chunks)} chunks in Neo4j...")
    print(f"Using model: {EMBED_MODEL}, batch_size: {BATCH_SIZE}")
    
    # Start timing the embedding/storage process
    start_time = time.time()
    
    # Set environment variables to ensure Neo4j credentials are available
    # This is the primary fix for the username issue
    os.environ['NEO4J_USER'] = NEO4J_USER
    os.environ['NEO4J_PASSWORD'] = NEO4J_PASSWORD
    os.environ['NEO4J_URI'] = NEO4J_URI
    
    # Process in batches with progress bar
    total_batches = (len(chunks) + BATCH_SIZE - 1) // BATCH_SIZE
    successful_batches = 0
    
    for i in tqdm(range(0, len(chunks), BATCH_SIZE), 
                  desc="Processing batches", 
                  total=total_batches):
        batch = chunks[i:i+BATCH_SIZE]
        try:
            # Method 1: Try with explicit parameters (most compatible)
            try:
                Neo4jVector.from_documents(
                    batch, embeddings,
                    url=NEO4J_URI, 
                    username=NEO4J_USER, 
                    password=NEO4J_PASSWORD,
                    index_name=INDEX_NAME, 
                    node_label=NODE_LABEL,
                    embedding_node_property="embedding", 
                    text_node_property="text"
                )
                successful_batches += 1
            except TypeError:
                # Method 2: Try without explicit username/password if the above fails
                # Some versions expect these to be in environment variables only
                Neo4jVector.from_documents(
                    batch, embeddings,
                    url=NEO4J_URI,
                    index_name=INDEX_NAME, 
                    node_label=NODE_LABEL,
                    embedding_node_property="embedding", 
                    text_node_property="text"
                )
                successful_batches += 1
                
        except Exception as e:
            tqdm.write(f"✗ Error processing batch {i//BATCH_SIZE + 1}: {e}")
            # Try alternative approach for this batch
            try:
                # Method 3: Initialize Neo4jVector separately then add documents
                vector_store = Neo4jVector(
                    embeddings,
                    url=NEO4J_URI,
                    username=NEO4J_USER,
                    password=NEO4J_PASSWORD,
                    index_name=INDEX_NAME,
                    node_label=NODE_LABEL,
                    embedding_node_property="embedding",
                    text_node_property="text"
                )
                vector_store.add_documents(batch)
                successful_batches += 1
                tqdm.write(f"✓ Batch {i//BATCH_SIZE + 1} processed with alternative method")
            except Exception as e2:
                tqdm.write(f"✗ Alternative method also failed for batch {i//BATCH_SIZE + 1}: {e2}")
                continue
    
    # Calculate and display timing
    elapsed_time = time.time() - start_time
    hours = elapsed_time / 3600
    minutes = (elapsed_time % 3600) / 60
    
    print(f"✓ Neo4j populated! Successfully processed {successful_batches}/{total_batches} batches")
    print(f"✓ Index: {INDEX_NAME}, Node Label: {NODE_LABEL}")
    print(f"✓ Embedding generation and storage took: {hours:.1f} hours ({minutes:.1f} minutes)")
    print(f"✓ Average time per chunk: {elapsed_time/len(chunks):.2f} seconds")


def verify_environment_variables():
    """Verify all required environment variables are set"""
    required_vars = ['NEO4J_URI', 'NEO4J_USER', 'NEO4J_PASSWORD']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please check your .env file or set these variables.")
        raise RuntimeError(f"Missing environment variables: {missing_vars}")
    
    print("✓ All required environment variables are set")


def check_dependencies():
    """Check if required packages for different file types are installed"""
    missing_packages = []
    
    # Check for PDF support
    try:
        import pypdf
    except ImportError:
        missing_packages.append("pypdf (for PDF files)")
    
    # Check for HTML/Markdown support
    try:
        import unstructured
    except ImportError:
        missing_packages.append("unstructured (for HTML and Markdown files)")
    
    # Check for web scraping support
    try:
        import bs4
    except ImportError:
        missing_packages.append("beautifulsoup4 (for web scraping)")
    
    if missing_packages:
        print(f"⚠ Missing optional packages: {', '.join(missing_packages)}")
        print("Install with: pip install pypdf unstructured beautifulsoup4")
        print("You can still process TXT files without these packages.")
    else:
        print("✓ All optional packages for file format support are installed")


def main():
    print("=" * 60)
    print("MULTI-FORMAT RAG DATA INGESTION WITH WIKI SCRAPING")
    print("=" * 60)
    print(f"Data directory: {DATA_DIR}")
    print(f"Neo4j URI: {NEO4J_URI}")
    print(f"Ollama URL: {OLLAMA_URL}")
    print(f"Embedding model: {EMBED_MODEL}")
    print(f"Supported formats: {', '.join(SUPPORTED_EXTENSIONS)}")
    print("=" * 60)
    
    # Ask user if they want to scrape wiki content first
    scrape_wiki = input("\nWould you like to scrape Dune wiki content first? (y/n): ").lower().strip()
    
    if scrape_wiki in ['y', 'yes']:
        print("\n🕷️  Starting wiki scraping...")
        wiki_dir = scrape_dune_wiki()
        if wiki_dir:
            print(f"✅ Wiki content scraped successfully!")
            print(f"✅ Wiki HTML files are now in: {wiki_dir}")
            print("✅ These will be included in the ingestion process")
        else:
            print("⚠️  Wiki scraping failed, continuing with existing files...")
    
    # Start timing the entire process
    total_start_time = time.time()
    
    # Verify environment variables first
    verify_environment_variables()
    
    # Check dependencies
    check_dependencies()
    
    # Create data directory if it doesn't exist
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # Create sample files if data directory is empty
    if not any(os.path.splitext(fn)[1].lower() in SUPPORTED_EXTENSIONS 
               for root, dirs, files in os.walk(DATA_DIR) 
               for fn in files):
        # Create sample TXT file
        with open(os.path.join(DATA_DIR, "dune_excerpt.txt"), "w", encoding='utf-8') as f:
            f.write("The spice must flow… Fear is the mind-killer. He who controls the spice controls the universe.")
        
        # Create sample Markdown file
        with open(os.path.join(DATA_DIR, "sample.md"), "w", encoding='utf-8') as f:
            f.write("# Sample Markdown\n\nThis is a **sample** markdown file for testing.\n\n## Features\n\n- Supports multiple formats\n- Automatic file type detection\n- Metadata preservation")
        
        print(f"✓ Created sample files in {DATA_DIR}")
    
    try:
        # Step 1: Clear existing data
        clear_start = time.time()
        clear_neo4j_database()
        clear_time = time.time() - clear_start
        print(f"✓ Database clearing took: {clear_time:.1f} seconds")
        
        # Step 2: Load and chunk documents
        chunk_start = time.time()
        chunks = load_and_chunk_documents()
        chunk_time = time.time() - chunk_start
        print(f"✓ Document loading and chunking took: {chunk_time:.1f} seconds")
        
        if not chunks:
            print("⚠ No chunks to process. Exiting.")
            return
        
        # Step 3: Generate embeddings and populate Neo4j
        populate_neo4j_with_chunks(chunks)
        
        # Calculate total time
        total_elapsed = time.time() - total_start_time
        total_hours = total_elapsed / 3600
        total_minutes = (total_elapsed % 3600) / 60
        
        print("\n" + "=" * 60)
        print("✅ INGESTION COMPLETE!")
        print(f"✅ Total processing time: {total_hours:.1f} hours ({total_minutes:.1f} minutes)")
        print(f"✅ Processed {len(chunks)} chunks total")
        
        # Show file type breakdown
        file_types = {}
        source_types = {}
        for chunk in chunks:
            file_type = chunk.metadata.get('file_type', 'unknown')
            source_type = chunk.metadata.get('source_type', 'local')
            file_types[file_type] = file_types.get(file_type, 0) + 1
            source_types[source_type] = source_types.get(source_type, 0) + 1
        
        print("✅ File type breakdown:")
        for file_type, count in file_types.items():
            print(f"   {file_type.upper()}: {count} chunks")
        
        print("✅ Source type breakdown:")
        for source_type, count in source_types.items():
            print(f"   {source_type.upper()}: {count} chunks")
        
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error during ingestion: {e}")
        raise


if __name__ == "__main__":
    main()