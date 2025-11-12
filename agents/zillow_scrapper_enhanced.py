"""
Enhanced ZillowScraper for Real Estate Agent Integration
Adds filter URL support to existing scraper

Key Additions:
1. Load pre-captured filter URLs from config
2. Build search URLs with filters dynamically
3. Fallback to manual URL building if no config found
"""

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
import random
from pathlib import Path
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class ZillowScraperWithFilters:
    """
    Enhanced Zillow scraper that supports pre-captured filter URLs
    Integrates seamlessly with LangGraph agent workflow
    """
    
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.driver = None
        self.config_dir = Path('zillow_configs')
        self.filter_configs = self._load_filter_configs()
    
    def _load_filter_configs(self) -> Dict:
        """Load saved filter configurations"""
        master_file = self.config_dir / 'all_filter_urls.json'
        
        if master_file.exists():
            try:
                with open(master_file, 'r') as f:
                    configs = json.load(f)
                    logger.info(f"✓ Loaded {len(configs)} filter configurations")
                    return {cfg['filter_name']: cfg for cfg in configs}
            except Exception as e:
                logger.warning(f"Failed to load filter configs: {e}")
        
        return {}
    
    def get_filter_url(self, 
                       zip_code: str,
                       status: str = "for_sale",
                       property_type: str = None,
                       bedrooms: int = None,
                       bathrooms: float = None) -> str:
        """
        Get search URL with filters applied
        
        Strategy:
        1. Try to find matching pre-captured filter config
        2. If found, replace ZIP in that URL
        3. If not found, build basic URL and log warning
        
        Args:
            zip_code: Target ZIP code
            status: "for_sale" or "sold"
            property_type: "houses", "townhomes", "apartments", etc.
            bedrooms: Minimum bedrooms
            bathrooms: Minimum bathrooms
        
        Returns:
            Complete Zillow search URL
        """
        
        # Try to find matching config
        config_key = self._build_config_key(status, property_type, bedrooms, bathrooms)
        
        if config_key in self.filter_configs:
            # Found matching config - use it!
            config = self.filter_configs[config_key]
            base_url = config['captured_url']
            
            # Replace the ZIP code in the URL
            # Zillow URLs typically have format: zillow.com/{location}/...
            # We need to replace the location part with our ZIP
            
            # Extract original location from config
            original_location = config['base_location']
            
            # Replace in URL
            new_url = base_url.replace(f"/{original_location}/", f"/{zip_code}/")
            
            logger.info(f"✓ Using pre-captured filter URL for {config_key}")
            return new_url
        
        else:
            # No matching config - build basic URL
            logger.warning(f"⚠️  No filter config found for {config_key}, using basic URL")
            logger.info("💡 Tip: Run zillow_filter_capture.py to capture this filter combination")
            
            # Build basic URL
            return self._build_basic_url(zip_code, status)
    
    def _build_config_key(self, status: str, property_type: str = None, 
                         bedrooms: int = None, bathrooms: float = None) -> str:
        """
        Build a key to match against saved configs
        
        Example keys:
        - "sold_houses_3bed_2bath"
        - "for_sale_townhomes"
        - "sold_all_types"
        """
        
        parts = [status]
        
        if property_type:
            parts.append(property_type.lower())
        
        if bedrooms:
            parts.append(f"{bedrooms}bed")
        
        if bathrooms:
            parts.append(f"{int(bathrooms)}bath")
        
        if len(parts) == 1:  # Just status
            parts.append("all_types")
        
        return "_".join(parts)
    
    def _build_basic_url(self, zip_code: str, status: str = "for_sale") -> str:
        """
        Fallback: Build basic URL without complex filters
        
        Args:
            zip_code: Target ZIP code
            status: "for_sale" or "sold"
        
        Returns:
            Basic Zillow search URL
        """
        
        base = f"https://www.zillow.com/{zip_code}/"
        
        # For sold properties, we'll need to click the filter in the browser
        # For now, just return base URL
        
        return base
    
    def init_driver(self):
        """Initialize undetected Chrome driver"""
        try:
            if self.driver:
                try:
                    self.driver.quit()
                    time.sleep(2)
                except:
                    pass
                self.driver = None
            
            options = uc.ChromeOptions()
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            
            if self.headless:
                options.add_argument('--headless=new')
            
            self.driver = uc.Chrome(options=options, use_subprocess=False)
            self.driver.set_page_load_timeout(120)
            self.driver.implicitly_wait(10)
            
            logger.info("✓ Chrome driver initialized")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize driver: {e}")
            return False
    
    def human_delay(self, min_seconds: int = 5, max_seconds: int = 10):
        """Add random delay"""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)
    
    def scroll_page(self):
        """Scroll page to load dynamic content"""
        try:
            total_height = self.driver.execute_script("return document.body.scrollHeight")
            viewport_height = self.driver.execute_script("return window.innerHeight")
            
            current_position = 0
            while current_position < total_height:
                self.driver.execute_script(f"window.scrollTo(0, {current_position});")
                time.sleep(random.uniform(1, 2))
                current_position += viewport_height
                
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height > total_height:
                    total_height = new_height
            
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)
            
        except Exception as e:
            logger.warning(f"Scroll error: {e}")
    
    def click_sold_filter(self) -> bool:
        """Click the 'Sold' filter on Zillow"""
        try:
            # Wait and click "For sale" dropdown
            for_sale_dropdown = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'For sale')]"))
            )
            for_sale_dropdown.click()
            time.sleep(2)
            
            # Click "Sold" option
            sold_option = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//label[contains(., 'Sold')]"))
            )
            sold_option.click()
            time.sleep(3)
            
            logger.info("✓ Clicked 'Sold' filter")
            return True
            
        except Exception as e:
            logger.warning(f"Failed to click sold filter: {e}")
            return False
    
    def get_property_urls_from_search(self, search_url: str, max_pages: int = 2) -> List[str]:
        """
        Extract property URLs from search results
        
        Args:
            search_url: Complete Zillow search URL
            max_pages: Max pages to scrape
        
        Returns:
            List of property detail URLs
        """
        property_urls = []
        
        try:
            self.driver.get(search_url)
            self.human_delay(5, 10)
            self.scroll_page()
            
            for page in range(max_pages):
                try:
                    WebDriverWait(self.driver, 30).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'a[href*="/homedetails/"]'))
                    )
                    
                    property_links = self.driver.find_elements(By.CSS_SELECTOR, 'a[href*="/homedetails/"]')
                    
                    if not property_links:
                        break
                    
                    for link in property_links:
                        try:
                            url = link.get_attribute('href')
                            if url:
                                url = url.split('?')[0].split('#')[0]
                                if url not in property_urls:
                                    property_urls.append(url)
                        except:
                            continue
                    
                    # Try next page
                    if page < max_pages - 1:
                        try:
                            next_button = self.driver.find_element(By.CSS_SELECTOR, 'a[rel="next"]')
                            if next_button and next_button.get_attribute('href'):
                                next_button.click()
                                self.human_delay(15, 22)
                                self.scroll_page()
                            else:
                                break
                        except:
                            break
                
                except Exception as e:
                    logger.error(f"Error on page {page + 1}: {e}")
                    break
            
            logger.info(f"✓ Collected {len(property_urls)} property URLs")
            return property_urls
        
        except Exception as e:
            logger.error(f"Error in get_property_urls_from_search: {e}")
            return property_urls
    
    def extract_property_details(self, property_url: str, retry_count: int = 2) -> Optional[Dict]:
        """
        Extract property details from detail page
        
        Args:
            property_url: Property detail page URL
            retry_count: Number of retries
        
        Returns:
            Property data dict or None
        """
        for attempt in range(retry_count):
            try:
                self.driver.get(property_url)
                self.human_delay(5, 10)
                
                property_data = {'url': property_url}
                
                # Try __NEXT_DATA__ extraction
                try:
                    script = self.driver.find_element(By.ID, '__NEXT_DATA__')
                    data = json.loads(script.get_attribute('innerHTML'))
                    
                    gdp_cache = data.get('props', {}).get('pageProps', {}).get('componentProps', {}).get('gdpClientCache')
                    
                    if gdp_cache:
                        gdp_data = json.loads(gdp_cache)
                        first_key = list(gdp_data.keys())[0]
                        prop_json = gdp_data[first_key].get('property', {})
                        
                        property_data.update({
                            'zpid': prop_json.get('zpid'),
                            'address': prop_json.get('address', {}).get('streetAddress'),
                            'city': prop_json.get('address', {}).get('city'),
                            'state': prop_json.get('address', {}).get('state'),
                            'zipcode': prop_json.get('address', {}).get('zipcode'),
                            'price': prop_json.get('price'),
                            'bedrooms': prop_json.get('bedrooms'),
                            'bathrooms': prop_json.get('bathrooms'),
                            'living_area': prop_json.get('livingArea'),
                            'home_type': prop_json.get('homeType'),
                            'home_status': prop_json.get('homeStatus'),
                            'year_built': prop_json.get('yearBuilt'),
                            'last_sold_price': prop_json.get('lastSoldPrice'),
                            'last_sold_date': prop_json.get('lastSoldDate'),
                        })
                        
                        return property_data
                
                except:
                    pass
                
                # HTML fallback
                try:
                    property_data['address'] = self._safe_extract(By.CSS_SELECTOR, 'h1', 'text')
                    property_data['price'] = self._safe_extract(By.CSS_SELECTOR, '[data-testid="price-header"]', 'text')
                    
                    if property_data.get('address'):
                        return property_data
                
                except:
                    pass
                
                if attempt < retry_count - 1:
                    time.sleep(30)
            
            except Exception as e:
                logger.error(f"Error extracting property (attempt {attempt + 1}): {e}")
                if attempt < retry_count - 1:
                    time.sleep(30)
        
        return None
    
    def _safe_extract(self, by: By, selector: str, attribute: str = 'text') -> Optional[str]:
        """Safely extract element"""
        try:
            element = self.driver.find_element(by, selector)
            return element.text if attribute == 'text' else element.get_attribute(attribute)
        except:
            return None
    
    def cleanup(self):
        """Clean up driver"""
        if self.driver:
            try:
                self.driver.quit()
                self.driver = None
                time.sleep(1)
            except Exception as e:
                logger.error(f"Error closing browser: {e}")


