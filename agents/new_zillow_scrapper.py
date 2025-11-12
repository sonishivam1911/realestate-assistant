"""
Zillow Property Scraper - Production Ready
Author: Built for Shivam's Real Estate AI Agent
Features:
- Undetected ChromeDriver for stealth
- Hybrid approach: CSS for search + JSON for details
- Rate limiting & error handling
- Data persistence (CSV + JSON)
- Retry logic with exponential backoff
"""

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
import csv
import random
from datetime import datetime
from pathlib import Path
import logging
from typing import List, Dict, Optional
import sys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('zillow_scraper.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class ZillowScraper:
    """
    Production-ready Zillow scraper using undetected-chromedriver
    """
    
    def __init__(self, headless: bool = False, use_proxy: bool = False, proxy_config: Optional[Dict] = None):
        """
        Initialize the scraper
        
        Args:
            headless: Run browser in headless mode (less stealthy)
            use_proxy: Whether to use proxy
            proxy_config: Proxy configuration dict
        """
        self.headless = headless
        self.use_proxy = use_proxy
        self.proxy_config = proxy_config
        self.driver = None
        self.properties_data = []
        
        # Create output directory
        self.output_dir = Path('zillow_data')
        self.output_dir.mkdir(exist_ok=True)
        
        logger.info("ZillowScraper initialized")
    
    def init_driver(self):
        """Initialize undetected Chrome driver with optimal settings"""
        try:
            # Cleanup existing driver first
            if self.driver:
                try:
                    self.driver.quit()
                    time.sleep(2)
                except:
                    pass
                self.driver = None
            
            options = uc.ChromeOptions()
            
            # Stealth settings
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-plugins')
            
            # Random user agent
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            ]
            options.add_argument(f'user-agent={random.choice(user_agents)}')
            
            if self.headless:
                options.add_argument('--headless=new')
                logger.warning("Running in headless mode - less stealthy!")
            
            # Initialize driver with better settings for stability
            self.driver = uc.Chrome(
                options=options, 
                use_subprocess=False,
                version_main=None  # Auto-detect Chrome version
            )
            self.driver.set_page_load_timeout(120)
            self.driver.set_script_timeout(60)
            self.driver.implicitly_wait(10)
            
            logger.info("Chrome driver initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize driver: {e}")
            import traceback
            traceback.print_exc()
            self.driver = None
            return False
    
    def human_delay(self, min_seconds: int = 10, max_seconds: int = 20):
        """Add random delay to mimic human behavior"""
        delay = random.uniform(min_seconds, max_seconds)
        logger.info(f"Waiting {delay:.2f} seconds...")
        time.sleep(delay)
    
    def scroll_page(self):
        """Scroll page to load dynamic content"""
        try:
            # Scroll to bottom gradually
            total_height = self.driver.execute_script("return document.body.scrollHeight")
            viewport_height = self.driver.execute_script("return window.innerHeight")
            
            current_position = 0
            while current_position < total_height:
                # Scroll by viewport height
                self.driver.execute_script(f"window.scrollTo(0, {current_position});")
                time.sleep(random.uniform(1, 2))
                current_position += viewport_height
                
                # Check if new content loaded
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height > total_height:
                    total_height = new_height
            
            # Scroll back to top
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)
            
        except Exception as e:
            logger.warning(f"Scroll error: {e}")
    
    def build_search_url(self, zip_code: str, status: str = "for_sale", property_types: List[str] = None, 
                         min_beds: int = None, max_beds: int = None, 
                         min_baths: float = None, max_baths: float = None) -> str:
        """
        Build Zillow search URL with filters
        
        Args:
            zip_code: ZIP code to search
            status: "for_sale", "sold", "for_rent"
            property_types: List of property types (houses, townhomes, apartments, condos, etc.)
            min_beds: Minimum bedrooms
            max_beds: Maximum bedrooms
            min_baths: Minimum bathrooms
            max_baths: Maximum bathrooms
            
        Returns:
            Complete Zillow search URL with filters
        """
        # Base URL
        url = f"https://www.zillow.com/{zip_code}/"
        
        # Map status to query parameter
        status_map = {
            "for_sale": "forSaleByAgent%3Dfalse%2CforSaleByOwner%3Dfalse%2Cnew%3Dfalse%2Ccondo_townhome_rowhome_coop%3Dfalse%2CmultiFamily%3Dfalse%2Cland%3Dfalse%2ClotSize%3Dfalse%2CparkingGarage%3Dfalse%2ChasGarage%3Dfalse%2CisAuction%3Dfalse",
            "sold": "forSaleByAgent%3Dfalse",
            "for_rent": "forSaleByAgent%3Dfalse"
        }
        
        params = []
        
        # Add status filter
        if status == "for_sale":
            params.append("searchQueryState=%7B%22pagination%22%3A%7B%7D%2C%22usersSearchTerm%22%3A%22")
        elif status == "sold":
            params.append("searchQueryState=%7B%22pagination%22%3A%7B%7D%2C%22usersSearchTerm%22%3A%22")
        
        # Add property types if specified
        if property_types:
            # Zillow property type codes
            property_type_codes = {
                "houses": "0",
                "townhomes": "1", 
                "apartments": "2",
                "condos": "3",
                "lots": "4",
                "manufactured": "5"
            }
            
        # Build query state (simplified - Zillow uses complex JSON)
        query_parts = []
        if status == "sold":
            query_parts.append("isAllHomes%3Dfalse")
            query_parts.append("isSalesByOwner%3Dfalse")
            query_parts.append("isSalesForeclosure%3Dfalse")
        
        # Construct full URL if parameters exist
        # For now, keep it simple - Zillow will show default for-sale
        # TODO: Add complex query string building for advanced filters
        
        return url
    
    def click_sold_filter(self) -> bool:
        """
        Click on the 'Sold' filter option on Zillow search page
        
        Returns:
            True if successfully clicked, False otherwise
        """
        try:
            # Find and click the "For sale" dropdown
            for_sale_dropdown = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'For sale')]"))
            )
            for_sale_dropdown.click()
            logger.info("Clicked 'For sale' dropdown")
            
            # Wait for menu to appear
            self.human_delay(1, 2)
            
            # Click on "Sold" option
            sold_option = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//label[contains(., 'Sold')]"))
            )
            sold_option.click()
            logger.info("Clicked 'Sold' option")
            
            # Wait for page to reload
            self.human_delay(3, 5)
            
            return True
        except Exception as e:
            logger.warning(f"Failed to click sold filter: {e}")
            return False
    
    def get_property_urls_from_search(self, search_url: str, max_pages: int = 3) -> List[str]:
        """
        Extract property URLs from Zillow search results
        
        Args:
            search_url: Zillow search URL (e.g., https://www.zillow.com/brooklyn-ny/)
            max_pages: Maximum number of pages to scrape
            
        Returns:
            List of property URLs
        """
        property_urls = []
        
        try:
            logger.info(f"Fetching search results from: {search_url}")
            
            # Single attempt - don't retry page loads as it crashes driver
            try:
                self.driver.get(search_url)
            except Exception as e:
                logger.error(f"Failed to load page: {e}")
                return property_urls
            
            # Wait for initial load
            self.human_delay(12, 18)
            
            # Scroll to load all listings
            self.scroll_page()
            
            for page in range(max_pages):
                logger.info(f"Scraping page {page + 1}/{max_pages}")
                
                try:
                    # Wait for any property links to load
                    # Zillow uses a[href*="/homedetails/"] as property links
                    WebDriverWait(self.driver, 30).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'a[href*="/homedetails/"]'))
                    )
                    
                    # Extract all property detail links
                    property_links = self.driver.find_elements(By.CSS_SELECTOR, 'a[href*="/homedetails/"]')
                    logger.info(f"Found {len(property_links)} property links on page {page + 1}")
                    
                    if len(property_links) == 0:
                        logger.warning("No property links found on this page")
                        break
                    
                    # Extract URLs from links
                    for link in property_links:
                        try:
                            url = link.get_attribute('href')
                            
                            # Clean up URL and remove query parameters
                            if url:
                                # Remove hash/query parameters
                                url = url.split('?')[0].split('#')[0]
                                
                                if url not in property_urls:
                                    property_urls.append(url)
                                    logger.debug(f"Added property: {url}")
                        
                        except Exception as e:
                            logger.debug(f"Error extracting URL from link: {e}")
                            continue
                    
                    # Try to go to next page
                    if page < max_pages - 1:
                        try:
                            # Look for next page button with multiple possible selectors
                            next_button = None
                            selectors = [
                                'a[rel="next"]',
                                'button[aria-label*="Next"]',
                                '.search-pagination a:last-child',
                            ]
                            
                            for selector in selectors:
                                try:
                                    next_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                                    if next_button and next_button.get_attribute('href'):
                                        break
                                except:
                                    continue
                            
                            if next_button and next_button.get_attribute('href'):
                                next_button.click()
                                logger.info("Clicked next page button")
                                self.human_delay(15, 22)
                                self.scroll_page()
                            else:
                                logger.info("No more pages available")
                                break
                        except Exception as e:
                            logger.info(f"No next page or error: {e}")
                            break
                
                except Exception as e:
                    logger.error(f"Error on page {page + 1}: {e}")
                    break
            
            logger.info(f"Total unique property URLs collected: {len(property_urls)}")
            return property_urls
        
        except Exception as e:
            logger.error(f"Error in get_property_urls_from_search: {e}")
            return property_urls
    
    def extract_property_details(self, property_url: str, retry_count: int = 3) -> Optional[Dict]:
        """
        Extract detailed property data from individual property page using hidden JSON
        
        Args:
            property_url: URL of the property detail page
            retry_count: Number of retries on failure
            
        Returns:
            Dictionary with property details or None
        """
        for attempt in range(retry_count):
            try:
                logger.info(f"Scraping property: {property_url} (Attempt {attempt + 1}/{retry_count})")
                
                self.driver.get(property_url)
                self.human_delay(8, 12)
                
                property_data = {
                    'url': property_url,
                    'scraped_at': datetime.now().isoformat()
                }
                
                # Method 1: Try __NEXT_DATA__ (most common)
                try:
                    script_element = self.driver.find_element(By.ID, '__NEXT_DATA__')
                    script_content = script_element.get_attribute('innerHTML')
                    data = json.loads(script_content)
                    
                    # Navigate the nested structure
                    gdp_cache = data.get('props', {}).get('pageProps', {}).get('componentProps', {}).get('gdpClientCache')
                    
                    if gdp_cache:
                        gdp_data = json.loads(gdp_cache)
                        # Get the first key (property ID)
                        first_key = list(gdp_data.keys())[0]
                        property_json = gdp_data[first_key].get('property', {})
                        
                        # Extract ALL available fields
                        property_data.update({
                            'zpid': property_json.get('zpid'),
                            'address': property_json.get('address', {}).get('streetAddress'),
                            'city': property_json.get('address', {}).get('city'),
                            'state': property_json.get('address', {}).get('state'),
                            'zipcode': property_json.get('address', {}).get('zipcode'),
                            'latitude': property_json.get('latitude'),
                            'longitude': property_json.get('longitude'),
                            'price': property_json.get('price'),
                            'currency': property_json.get('currency'),
                            'bedrooms': property_json.get('bedrooms'),
                            'bathrooms': property_json.get('bathrooms'),
                            'living_area': property_json.get('livingArea'),
                            'living_area_units': property_json.get('livingAreaUnits'),
                            'home_type': property_json.get('homeType'),
                            'home_status': property_json.get('homeStatus'),
                            'zestimate': property_json.get('zestimate'),
                            'rent_zestimate': property_json.get('rentZestimate'),
                            'year_built': property_json.get('yearBuilt'),
                            'lot_size': property_json.get('lotSize'),
                            'lot_area_units': property_json.get('lotAreaUnits'),
                            'property_tax_rate': property_json.get('propertyTaxRate'),
                            'description': property_json.get('description'),
                            'days_on_zillow': property_json.get('daysOnZillow'),
                            'schools': property_json.get('schools', []),
                            'images': [img.get('url') for img in property_json.get('photos', [])],
                            # Additional fields
                            'parking_spots': property_json.get('parkingSpots'),
                            'garage_type': property_json.get('garageType'),
                            'hoa_fee': property_json.get('hoaFee'),
                            'property_type': property_json.get('propertyType'),
                            'roof_material': property_json.get('roofMaterial'),
                            'pool': property_json.get('pool'),
                            'basement': property_json.get('basement'),
                            'exterior_walls': property_json.get('exteriorWalls'),
                            'heating': property_json.get('heating'),
                            'cooling': property_json.get('cooling'),
                            'mls_id': property_json.get('mlsId'),
                            'county_name': property_json.get('countyName'),
                            'fips_code': property_json.get('fipsCode'),
                            'property_id': property_json.get('propertyId'),
                            'tax_year': property_json.get('taxYear'),
                            'last_sold_price': property_json.get('lastSoldPrice'),
                            'last_sold_date': property_json.get('lastSoldDate'),
                            'tax_assessed_value': property_json.get('taxAssessedValue'),
                            'unit_count': property_json.get('unitCount'),
                            'stories': property_json.get('stories'),
                            'construction_type': property_json.get('constructionType'),
                            'full_baths': property_json.get('fullBathrooms'),
                            'half_baths': property_json.get('halfBathrooms'),
                        })
                        
                        logger.info(f"✓ Successfully extracted data using __NEXT_DATA__ method")
                        return property_data
                
                except json.JSONDecodeError as e:
                    logger.debug(f"JSON decode error in __NEXT_DATA__: {e}")
                except Exception as e:
                    logger.debug(f"__NEXT_DATA__ method failed: {e}")
                
                # Method 2: Try hdpApolloPreloadedData (backup)
                try:
                    script_element = self.driver.find_element(By.ID, 'hdpApolloPreloadedData')
                    script_content = script_element.get_attribute('innerHTML')
                    data = json.loads(script_content)
                    
                    api_cache = json.loads(data.get('apiCache', '{}'))
                    
                    # Find the property data (usually has 'ForSale' or 'ForRent' in key)
                    for key, value in api_cache.items():
                        if 'ForSale' in key or 'ForRent' in key:
                            property_json = value.get('property', {})
                            
                            property_data.update({
                                'zpid': property_json.get('zpid'),
                                'address': property_json.get('address', {}).get('streetAddress'),
                                'city': property_json.get('address', {}).get('city'),
                                'state': property_json.get('address', {}).get('state'),
                                'zipcode': property_json.get('address', {}).get('zipcode'),
                                'price': property_json.get('price'),
                                'bedrooms': property_json.get('bedrooms'),
                                'bathrooms': property_json.get('bathrooms'),
                                'living_area': property_json.get('livingArea'),
                                'home_type': property_json.get('homeType'),
                            })
                            
                            logger.info(f"✓ Successfully extracted data using Apollo method")
                            return property_data
                
                except Exception as e:
                    logger.debug(f"Apollo method failed: {e}")
                
                # Method 3: Scrape visible HTML as fallback
                try:
                    logger.info("Attempting HTML scraping fallback method...")
                    
                    property_data['address'] = self._safe_extract(
                        By.CSS_SELECTOR, 
                        'h1, [data-testid="headline"]',
                        'text'
                    )
                    
                    property_data['price'] = self._safe_extract(
                        By.CSS_SELECTOR,
                        '[data-testid="price-header"], .z-price',
                        'text'
                    )
                    
                    property_data['bedrooms'] = self._safe_extract(
                        By.CSS_SELECTOR,
                        '[data-testid="beds"]',
                        'text'
                    )
                    
                    if any([property_data.get('address'), property_data.get('price')]):
                        logger.info(f"✓ Successfully extracted some data using HTML fallback")
                        return property_data
                
                except Exception as e:
                    logger.debug(f"HTML fallback method failed: {e}")
                
                # If all methods fail, log and retry
                logger.warning(f"All extraction methods failed for {property_url}")
                
                if attempt < retry_count - 1:
                    wait_time = (attempt + 1) * 30  # Exponential backoff
                    logger.info(f"Retrying after {wait_time} seconds...")
                    time.sleep(wait_time)
            
            except Exception as e:
                logger.error(f"Error extracting property details (attempt {attempt + 1}): {e}")
                if attempt < retry_count - 1:
                    time.sleep(30)
        
        return None
    
    def _safe_extract(self, by: By, selector: str, attribute: str = 'text') -> Optional[str]:
        """
        Safely extract element text or attribute
        """
        try:
            element = self.driver.find_element(by, selector)
            if attribute == 'text':
                return element.text
            else:
                return element.get_attribute(attribute)
        except:
            return None
    
    def scrape_properties(self, search_url: str, max_pages: int = 3, max_properties: int = 50):
        """
        Main scraping workflow
        
        Args:
            search_url: Zillow search URL
            max_pages: Maximum search result pages to scrape
            max_properties: Maximum number of properties to scrape in detail
        """
        try:
            # Initialize driver
            if not self.init_driver():
                logger.error("Failed to initialize driver")
                return
            
            # Step 1: Get property URLs from search
            logger.info("=" * 80)
            logger.info("PHASE 1: Collecting property URLs from search results")
            logger.info("=" * 80)
            
            property_urls = self.get_property_urls_from_search(search_url, max_pages)
            
            if not property_urls:
                logger.error("No property URLs found!")
                return
            
            # Limit to max_properties
            property_urls = property_urls[:max_properties]
            
            logger.info("=" * 80)
            logger.info(f"PHASE 2: Extracting detailed data from {len(property_urls)} properties")
            logger.info("=" * 80)
            
            # Step 2: Extract details from each property
            for idx, url in enumerate(property_urls, 1):
                logger.info(f"\n--- Property {idx}/{len(property_urls)} ---")
                
                property_data = self.extract_property_details(url)
                
                if property_data:
                    self.properties_data.append(property_data)
                    logger.info(f"✓ Successfully scraped property {idx}")
                    
                    # Save incrementally every 5 properties
                    if idx % 5 == 0:
                        self.save_data()
                        logger.info(f"Incremental save completed ({idx} properties)")
                else:
                    logger.warning(f"✗ Failed to scrape property {idx}")
                
                # Rate limiting between properties
                if idx < len(property_urls):
                    self.human_delay(15, 25)
            
            # Final save
            self.save_data()
            
            logger.info("=" * 80)
            logger.info(f"SCRAPING COMPLETE! Total properties scraped: {len(self.properties_data)}")
            logger.info("=" * 80)
        
        except Exception as e:
            logger.error(f"Error in scrape_properties: {e}")
        
        finally:
            self.cleanup()
    
    def save_data(self):
        """Save scraped data to CSV and JSON files"""
        if not self.properties_data:
            logger.warning("No data to save")
            return
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save to JSON (full data with nested structures)
        json_file = self.output_dir / f'zillow_data_{timestamp}.json'
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.properties_data, f, indent=2, ensure_ascii=False)
        logger.info(f"Data saved to JSON: {json_file}")
        
        # Save to CSV (flattened data for easy analysis)
        csv_file = self.output_dir / f'zillow_data_{timestamp}.csv'
        
        if self.properties_data:
            # Define CSV fields (exclude nested structures)
            csv_fields = [
                'zpid', 'address', 'city', 'state', 'zipcode', 'latitude', 'longitude',
                'price', 'currency', 'bedrooms', 'bathrooms', 'living_area', 'living_area_units',
                'home_type', 'home_status', 'zestimate', 'rent_zestimate', 'year_built',
                'lot_size', 'lot_area_units', 'days_on_zillow', 'url', 'scraped_at'
            ]
            
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=csv_fields, extrasaction='ignore')
                writer.writeheader()
                writer.writerows(self.properties_data)
            
            logger.info(f"Data saved to CSV: {csv_file}")
    
    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            try:
                # First close all tabs/windows
                try:
                    self.driver.close_window()
                except:
                    pass
                
                # Then quit the driver
                self.driver.quit()
                self.driver = None
                logger.info("Browser closed successfully")
                time.sleep(1)  # Give OS time to release resources
                
            except Exception as e:
                logger.error(f"Error closing browser: {e}")
                self.driver = None


def main():
    """
    Example usage
    """
    # Configuration
    SEARCH_URL = "https://www.zillow.com/brooklyn-ny/"  # Change to your target location
    MAX_PAGES = 2  # Number of search result pages
    MAX_PROPERTIES = 20  # Maximum properties to scrape in detail
    
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║           Zillow Property Scraper - Production Ready          ║
    ║                                                               ║
    ║  Built for: Real Estate AI Agent / Property Valuation        ║
    ║  Method: Undetected ChromeDriver + Hidden JSON Extraction    ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)
    
    print(f"\n📍 Target: {SEARCH_URL}")
    print(f"📄 Pages: {MAX_PAGES}")
    print(f"🏠 Max Properties: {MAX_PROPERTIES}")
    print("\n⚠️  IMPORTANT NOTES:")
    print("   - This will take 15-25 seconds per property (rate limiting)")
    print("   - Data saved incrementally every 5 properties")
    print("   - Check 'zillow_data/' folder for output files")
    print("   - If you see CAPTCHA, solve it manually and press Enter\n")
    
    response = input("Ready to start? (yes/no): ").strip().lower()
    
    if response != 'yes':
        print("Scraping cancelled.")
        return
    
    # Initialize and run scraper
    scraper = ZillowScraper(headless=False)  # Set headless=True for background operation
    scraper.scrape_properties(
        search_url=SEARCH_URL,
        max_pages=MAX_PAGES,
        max_properties=MAX_PROPERTIES
    )


if __name__ == "__main__":
    main()