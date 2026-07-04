"""
Ultimate Zillow Scraper with Legal ZIP Boundary Fetching
PYTHON 3.13 COMPATIBLE VERSION

This version uses pgeocode library (100% legal, Python 3.13 compatible!)

Key Changes:
1. Uses pgeocode for boundary data (legal & free)
2. No calls to Zillow's internal APIs
3. Still builds proper searchQueryState URLs
4. Still includes boundary lock to prevent redirects
5. Python 3.13 compatible!

Install: pip install pgeocode
"""

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
import random
import urllib.parse
from pathlib import Path
from typing import List, Dict, Optional
import logging

# Legal boundary fetching - Python 3.13 compatible!
import pgeocode

logger = logging.getLogger(__name__)


class LegalZIPBoundaryFetcher:
    """
    Fetches ZIP code boundaries using pgeocode library
    100% legal, Python 3.13 compatible!
    """
    
    def __init__(self):
        # Initialize pgeocode for US
        self.nomi = pgeocode.Nominatim('us')
        logger.info("✓ Initialized pgeocode (legal boundary source, Python 3.13 compatible)")
    
    def get_zip_info(self, zip_code: str, status: str = "for_sale") -> Optional[Dict]:
        """
        Get ZIP code boundaries and info from pgeocode
        
        Args:
            zip_code: 5-digit ZIP code
            status: "for_sale" or "sold" - affects boundary size
        
        Returns:
            Dict with mapBounds and metadata, or None if not found
        """
        try:
            # Query the ZIP code
            result = self.nomi.query_postal_code(zip_code)
            
            # Check if found
            if result is None or result.empty or result.isna().all():
                logger.warning(f"⚠️  ZIP code {zip_code} not found")
                return None
            
            # Get coordinates
            lat = result.get('latitude')
            lng = result.get('longitude')
            
            if lat is None or lng is None or (isinstance(lat, float) and lat != lat):
                logger.warning(f"⚠️  No coordinates found for ZIP {zip_code}")
                return None
            
            if status == "sold":
                lat_margin = 0.08   
                lng_margin = 0.12  
                logger.info(f"🔍 Using EXPANDED boundaries for sold listings")
            else:
                lat_margin = 0.05   
                lng_margin = 0.05   

            # Create approximate boundaries
            zip_info = {
                "mapBounds": {
                    "west": lng - lng_margin,
                    "east": lng + lng_margin,
                    "south": lat - lat_margin,
                    "north": lat + lat_margin
                },
                # Zillow uses regionType 7 for ZIP codes
                "regionType": 7,
                "regionId": None,
                # Extra metadata
                "metadata": {
                    "city": result.get('place_name'),
                    "state": result.get('state_code'),
                    "county": result.get('county_name'),
                    "lat": lat,
                    "lng": lng
                }
            }
            
            logger.info(f"✓ Found coordinates for ZIP {zip_code}")
            logger.debug(f"  Center: ({lat}, {lng})")
            logger.debug(f"  Location: {result.get('place_name')}, {result.get('state_code')}")
            
            return zip_info
            
        except Exception as e:
            logger.error(f"❌ Error fetching ZIP info: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return None


class UltimateZillowScraper:
    """
    Production-ready Zillow scraper with LEGAL ZIP boundary locking
    Python 3.13 compatible version using pgeocode!
    """
    
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.driver = None
        self.config_dir = Path('zillow_configs')
        self.filter_configs = self._load_filter_configs()
        
        # Use LEGAL boundary fetcher (Python 3.13 compatible)!
        self.boundary_fetcher = LegalZIPBoundaryFetcher()
        
        # Cache ZIP boundaries
        self.zip_boundary_cache = {}
    
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
    
    def _get_zip_boundaries(self, zip_code: str, status: str = "for_sale") -> Optional[Dict]:
        """
        Get ZIP code boundaries with caching
        Uses pgeocode library (legal and Python 3.13 compatible!)
        
        Args:
            zip_code: 5-digit ZIP code
            status: "for_sale" or "sold"
        
        Returns:
            Dict with mapBounds
        """
        # Check cache first
        cache_key = f"{zip_code}_{status}"  # ✅ Different cache for sold vs for-sale
        if cache_key in self.zip_boundary_cache:
            logger.debug(f"✓ Using cached boundaries for {cache_key}")
            return self.zip_boundary_cache[cache_key]
        
        # Fetch from pgeocode
        zip_info = self.boundary_fetcher.get_zip_info(zip_code, status)  # ✅ Pass status
        
        if zip_info:
            # Cache it
            self.zip_boundary_cache[cache_key] = zip_info
            logger.info(f"✓ Cached boundaries for {cache_key}")
        
        return zip_info
    
    # def _get_zip_boundaries(self, zip_code: str) -> Optional[Dict]:
    #     """
    #     Get ZIP code boundaries with caching
    #     Uses pgeocode library (legal and Python 3.13 compatible!)
        
    #     Args:
    #         zip_code: 5-digit ZIP code
        
    #     Returns:
    #         Dict with mapBounds
    #     """
    #     # Check cache first
    #     if zip_code in self.zip_boundary_cache:
    #         logger.debug(f"✓ Using cached boundaries for {zip_code}")
    #         return self.zip_boundary_cache[zip_code]
        
    #     # Fetch from pgeocode
    #     zip_info = self.boundary_fetcher.get_zip_info(zip_code)
        
    #     if zip_info:
    #         # Cache it
    #         self.zip_boundary_cache[zip_code] = zip_info
    #         logger.info(f"✓ Cached boundaries for {zip_code}")
        
    #     return zip_info
    
    def build_zillow_url(self, 
                        zip_code: str,
                        status: str = "for_sale",
                        property_type: str = None,
                        min_beds: int = None,
                        min_baths: float = None,
                        min_price: int = None,
                        max_price: int = None,
                        min_sqft: int = None,
                        max_sqft: int = None,
                        days_back: int = 180) -> str:
        """
        Build a proper Zillow filter URL with ZIP boundary lock
        Uses pgeocode for boundaries (100% legal, Python 3.13 compatible!)
        
        Args:
            zip_code: Target ZIP code (5 digits)
            status: "for_sale" or "sold"
            days_back: For sold homes, how many days back to look (default: 180 days / 6 months)

            property_type: "houses", "townhomes", "condos", "apartments", etc.
            min_beds: Minimum bedrooms
            min_baths: Minimum bathrooms
            min_price: Minimum price
            max_price: Maximum price
            min_sqft: Minimum square footage
            max_sqft: Maximum square footage
        
        Returns:
            Complete Zillow URL with encoded filters and boundary lock
        """
        
        # Validate ZIP code
        if not isinstance(zip_code, str) or not zip_code.isdigit() or len(zip_code) != 5:
            logger.error(f"❌ INVALID ZIP CODE: '{zip_code}'. Must be exactly 5 digits.")
            raise ValueError(f"Invalid ZIP code format: {zip_code}")
        
        # Get ZIP boundaries using LEGAL method!
        logger.info(f"🔒 Fetching boundaries for ZIP {zip_code} (using pgeocode)...")
        zip_info = self._get_zip_boundaries(zip_code, status)
        
        if not zip_info:
            logger.warning(f"⚠️  Failed to get boundaries for {zip_code}")
            logger.warning(f"⚠️  URL will be built WITHOUT boundary lock")
            logger.warning(f"⚠️  This may cause Zillow to redirect to broader area!")
        
        # ✅ Build searchQueryState with boundary lock (SAME for both for-sale and sold)
        search_state = {
            "pagination": {},
            "isMapVisible": True,
            "filterState": {}
        }
        
        # Add boundary lock if we got the info
        if zip_info and zip_info.get("mapBounds"):
            search_state["mapBounds"] = zip_info["mapBounds"]
            logger.info(f"✓ Boundary lock applied using pgeocode data")
            
            # Log the location info
            if zip_info.get("metadata"):
                meta = zip_info["metadata"]
                logger.info(f"  Location: {meta.get('city')}, {meta.get('state')}")
        
        # Property type filters
        if property_type:
            logger.info(f"🐛 APPLYING PROPERTY TYPE FILTER: {property_type}")
            type_map = {
                "houses": "sf",
                "house": "sf",
                "single_family": "sf",
                "single family": "sf",
                "townhouse": "tow",
                "townhomes": "tow",
                "condo": "con",
                "condos": "con",
                "multi_family": "mf",
                "multi family": "mf",
                "apartment": "apco",
                "apartments": "apco",
                "land": "land",
                "manufactured": "manu"
            }
            
            all_types = ["sf", "mf", "con", "apco", "land", "tow", "manu"]
            for ptype in all_types:
                search_state["filterState"][ptype] = {"value": False}
            
            ptype_lower = property_type.lower().strip()
            if ptype_lower in type_map:
                zillow_code = type_map[ptype_lower]
                search_state["filterState"][zillow_code] = {"value": True}
                logger.info(f"   ✅ Property Type Filter: {property_type} → Zillow code '{zillow_code}' SET TO TRUE")
            else:
                logger.warning(f"   ⚠️  Unknown property type: {property_type}")
        else:
            logger.info(f"🐛 NO PROPERTY TYPE FILTER APPLIED (property_type is None/empty)")
        
        # Bedroom filter
        if min_beds:
            logger.info(f"🐛 APPLYING BEDROOM FILTER: min_beds={min_beds}")
            search_state["filterState"]["beds"] = {"min": min_beds}
        else:
            logger.info(f"🐛 NO BEDROOM FILTER APPLIED (min_beds is None/0)")
        
        # Bathroom filter
        if min_baths:
            logger.info(f"🐛 APPLYING BATHROOM FILTER: min_baths={min_baths}")
            search_state["filterState"]["baths"] = {"min": min_baths}
        else:
            logger.info(f"🐛 NO BATHROOM FILTER APPLIED (min_baths is None/0)")
        
        # Price filters
        if min_price or max_price:
            search_state["filterState"]["price"] = {}
            if min_price:
                search_state["filterState"]["price"]["min"] = min_price
            if max_price:
                search_state["filterState"]["price"]["max"] = max_price
        
        # Square footage filters
        if min_sqft or max_sqft:
            search_state["filterState"]["sqft"] = {}
            if min_sqft:
                search_state["filterState"]["sqft"]["min"] = min_sqft
            if max_sqft:
                search_state["filterState"]["sqft"]["max"] = max_sqft
        
        # Status filter - SIMPLE: just add rs=true for sold, rs=false for for-sale
        if status == "sold":
            search_state["filterState"]["rs"] = {"value": True}
            logger.info(f"   ✅ Sold filter: rs=True")
        else:
            search_state["filterState"]["rs"] = {"value": False}
            logger.info(f"   ✅ For-sale filter: rs=False")
        
        # Convert to JSON and URL encode
        json_str = json.dumps(search_state, separators=(',', ':'))
        encoded = urllib.parse.quote(json_str)
        
        # ✅ DEBUG: Log the complete filter state before URL generation
        logger.info(f"🐛 COMPLETE FILTER STATE DEBUG:")
        for key, value in search_state["filterState"].items():
            logger.info(f"   {key}: {value}")
        

        if status == "sold":
            url = f"https://www.zillow.com/homes/recently_sold/?searchQueryState={encoded}"
            logger.info(f"   ✅ Using sold URL: /homes/recently_sold/")
        else:
            url = f"https://www.zillow.com/{zip_code}/?searchQueryState={encoded}"
            logger.info(f"   ✅ Using for-sale URL: {zip_code}/")
        
        # LOG THE URL FOR DEBUGGING
        logger.info(f"\n{'='*80}")
        logger.info(f"🔨 BUILT SEARCH URL:")
        logger.info(f"   ZIP: {zip_code}")
        logger.info(f"   Boundary Lock: {'✓ ENABLED (pgeocode)' if zip_info else '✗ DISABLED'}")
        logger.info(f"   Status: {status}")
        logger.info(f"   Property Type: {property_type}")
        logger.info(f"   Filters: beds={min_beds}, baths={min_baths}, price={min_price}-{max_price}, sqft={min_sqft}-{max_sqft}")
        
        # ✅ DEBUG: Show exactly what parameters were received
        logger.info(f"🐛 RECEIVED PARAMETERS:")
        logger.info(f"   property_type={property_type} (type: {type(property_type)})")
        logger.info(f"   min_beds={min_beds} (type: {type(min_beds)})")
        logger.info(f"   min_baths={min_baths} (type: {type(min_baths)})")
        logger.info(f"   min_price={min_price}, max_price={max_price}")
        logger.info(f"   days_back={days_back}")
        
        if zip_info and zip_info.get("mapBounds"):
            bounds = zip_info["mapBounds"]
            logger.info(f"\n🗺️  Map Bounds (from pgeocode):")
            logger.info(f"   North: {bounds['north']}")
            logger.info(f"   South: {bounds['south']}")
            logger.info(f"   East: {bounds['east']}")
            logger.info(f"   West: {bounds['west']}")
        
        logger.info(f"\n📋 Filter State: {json.dumps(search_state['filterState'], indent=2)}")
        logger.info(f"\n🌐 Full URL: {url[:200]}...")
        logger.info(f"{'='*80}\n")
        
        return url
    
    def init_driver(self):
        """Initialize undetected Chrome driver with timeout handling"""
        try:
            import os
            import shutil
            
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
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-web-resources')
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-plugins')
            
            if self.headless:
                options.add_argument('--headless=new')
            
            # ✅ Find Chrome binary path using multiple strategies
            chrome_binary = None
            
            # Strategy 1: Check common system paths
            chrome_paths = [
                '/usr/bin/google-chrome',
                '/usr/bin/google-chrome-stable',
                '/usr/bin/chromium',
                '/usr/bin/chromium-browser',
                '/snap/bin/chromium',
                '/usr/local/bin/chromium',
                '/opt/google/chrome/chrome',
            ]
            
            for path in chrome_paths:
                if os.path.exists(path):
                    chrome_binary = path
                    logger.info(f"✓ Found Chrome binary at: {path}")
                    break
            
            # Strategy 2: Use 'which' command to find chrome
            if not chrome_binary:
                try:
                    chrome_which = shutil.which('google-chrome') or shutil.which('chromium') or shutil.which('chromium-browser')
                    if chrome_which:
                        chrome_binary = chrome_which
                        logger.info(f"✓ Found Chrome using 'which': {chrome_binary}")
                except:
                    pass
            
            # Strategy 3: Set binary location ONLY if found (avoid None)
            if chrome_binary and isinstance(chrome_binary, str):
                options.binary_location = chrome_binary
                logger.info(f"✓ Set Chrome binary location: {chrome_binary}")
            else:
                logger.warning("⚠️  Chrome binary not found - letting undetected-chromedriver auto-detect")
            
            # ✅ Set timeout environment variable
            os.environ['REQUESTS_TIMEOUT'] = '45'
            
            # Initialize driver without specifying binary if not found
            self.driver = uc.Chrome(options=options, use_subprocess=False, version_main=None)
            
            # ✅ Set timeouts
            self.driver.set_page_load_timeout(45)
            self.driver.set_script_timeout(30)
            self.driver.implicitly_wait(10)
            
            logger.info("✓ Chrome driver initialized successfully (45s page load timeout)")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize driver: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            self.driver = None
            return False
    
    def human_delay(self, min_seconds: int = 2, max_seconds: int = 5):
        """Add random delay to mimic human behavior"""
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
    
    def verify_location(self, expected_zip: str) -> bool:
        """Verify that we're actually on the correct ZIP code page"""
        try:
            actual_url = self.driver.current_url
            
            import re
            # More specific regex: look for 5-digit ZIP code right after zillow.com/
            match = re.search(r'zillow\.com/(\d{5})', actual_url)
            
            if match:
                url_zip = match.group(1)
                
                if url_zip == expected_zip:
                    logger.info(f"✓ Location verified: {expected_zip}")
                    return True
                else:
                    logger.error(f"❌ LOCATION MISMATCH!")
                    logger.error(f"   Expected: {expected_zip}")
                    logger.error(f"   Got: {url_zip}")
                    return False
            
            # If we can't find a ZIP in the URL, that's also a mismatch
            logger.warning(f"⚠️  Could not extract ZIP code from URL: {actual_url}")
            return False
            
        except Exception as e:
            logger.warning(f"Could not verify location: {e}")
            return False
    
    def get_property_urls_from_search(self, search_url: str, max_pages: int = 2) -> List[str]:
        """Extract property URLs from search results - NO RETRY on timeout"""
        property_urls = []
        
        try:
            logger.info(f"Loading search URL...")
            
            import re
            zip_match = re.search(r'zillow\.com/(\d{5})', search_url)
            expected_zip = zip_match.group(1) if zip_match else None
            
            if expected_zip:
                logger.info(f"🎯 Target ZIP: {expected_zip}")
            
            # ✅ CRITICAL: Check if driver is still connected before use
            if not self.driver:
                logger.error("❌ Driver is None - reinitializing...")
                if not self.init_driver():
                    return property_urls
            
            # ✅ Test driver connection - if broken, reinitialize immediately
            try:
                self.driver.current_url
            except Exception as e:
                logger.warning(f"⚠️  Driver connection lost: {str(e)[:50]} - reinitializing...")
                try:
                    self.cleanup()
                except:
                    pass
                time.sleep(2)
                if not self.init_driver():
                    return property_urls
            
            # ✅ Handle page load with timeout - NO RETRY, just continue or skip
            try:
                logger.info(f"📡 Fetching page (45s timeout)...")
                self.driver.get(search_url)
                logger.info(f"✓ Page loaded successfully")
                    
            except TimeoutError as e:
                logger.warning(f"⚠️  Page load timeout (45s) - SKIPPING THIS ZIP (no retry)")
                return property_urls  # ✅ Skip entire ZIP on timeout, no retry
                        
            except Exception as e:
                # ✅ Connection errors should trigger driver restart
                error_str = str(e)
                if 'HTTPConnectionPool' in error_str or 'localhost' in error_str:
                    logger.error(f"❌ Driver connection error: {error_str[:100]}")
                    try:
                        self.cleanup()
                    except:
                        pass
                    self.driver = None
                else:
                    logger.error(f"❌ Failed to load page: {error_str[:100]}")
                return property_urls
            
            # If we got here, page loaded - extract URLs
            self.human_delay(3, 5)
            
            if expected_zip:
                if not self.verify_location(expected_zip):
                    logger.error("❌ Failed location verification!")
                    return property_urls
            
            try:
                self.scroll_page()
            except Exception as e:
                logger.warning(f"⚠️  Scroll failed: {str(e)[:50]} - continuing...")
            
            for page in range(max_pages):
                try:
                    WebDriverWait(self.driver, 20).until(
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
                    
                    if page < max_pages - 1:
                        try:
                            next_button = self.driver.find_element(By.CSS_SELECTOR, 'a[rel="next"]')
                            if next_button and next_button.get_attribute('href'):
                                next_button.click()
                                self.human_delay(3, 5)
                                
                                if expected_zip:
                                    self.verify_location(expected_zip)
                                
                                try:
                                    self.scroll_page()
                                except:
                                    pass
                            else:
                                break
                        except:
                            break
                
                except TimeoutError:
                    logger.warning(f"⚠️  Wait timeout on page {page + 1} - moving to next page")
                    break
                except Exception as e:
                    logger.error(f"Error on page {page + 1}: {str(e)[:50]}")
                    break
            
            logger.info(f"✓ Collected {len(property_urls)} property URLs")
            return property_urls
        
        except Exception as e:
            logger.error(f"Error in get_property_urls_from_search: {e}")
            return property_urls
    
    def extract_property_details(self, property_url: str, retry_count: int = 1) -> Optional[Dict]:
        """Extract property details from detail page - NO RETRY on timeout"""
        for attempt in range(retry_count):
            try:
                logger.info(f"📄 Fetching details (45s timeout)...")
                
                try:
                    self.driver.get(property_url)
                    logger.info(f"✓ Property page loaded")
                except TimeoutError as e:
                    logger.warning(f"⚠️  Property page load timeout: SKIPPING THIS PROPERTY (no retry)")
                    return None  # ✅ Skip property on timeout, no retry
                except Exception as e:
                    logger.error(f"❌ Failed to load property page: {str(e)[:50]}")
                    return None
                
                self.human_delay(2, 4)
                
                # ✅ Store the property link/URL from the start
                property_data = {
                    'url': property_url,
                    'link': property_url  # ✅ Also store as 'link' for compatibility
                }
                
                try:
                    script = self.driver.find_element(By.ID, '__NEXT_DATA__')
                    data = json.loads(script.get_attribute('innerHTML'))
                    
                    gdp_cache = data.get('props', {}).get('pageProps', {}).get('componentProps', {}).get('gdpClientCache')
                    
                    if gdp_cache:
                        gdp_data = json.loads(gdp_cache)
                        first_key = list(gdp_data.keys())[0]
                        prop_json = gdp_data[first_key].get('property', {})
                        
                        # ✅ Extract square footage - CRITICAL for valuation!
                        living_area_sqft = prop_json.get('livingArea')
                        price = prop_json.get('price')
                        
                        property_data.update({
                            'zpid': prop_json.get('zpid'),
                            'address': prop_json.get('address', {}).get('streetAddress'),
                            'city': prop_json.get('address', {}).get('city'),
                            'state': prop_json.get('address', {}).get('state'),
                            'zipcode': prop_json.get('address', {}).get('zipcode'),
                            'price': price,
                            'bedrooms': prop_json.get('bedrooms'),
                            'bathrooms': prop_json.get('bathrooms'),
                            'living_area_sqft': living_area_sqft,  # ✅ Use correct key name
                            'home_type': prop_json.get('homeType'),
                            'home_status': prop_json.get('homeStatus'),
                            'year_built': prop_json.get('yearBuilt'),
                            'last_sold_price': prop_json.get('lastSoldPrice'),
                            'last_sold_date': prop_json.get('lastSoldDate'),
                        })
                        
                        # ✅ CALCULATE PRICE PER SQUARE FOOT (used in valuation)
                        if price and living_area_sqft and living_area_sqft > 0:
                            property_data['price_per_sqft'] = round(price / living_area_sqft, 2)
                            logger.info(f"✅ Price/sqft calculated: ${property_data['price_per_sqft']:.2f}/sqft")
                        
                        # ✅ Log extracted square footage for verification
                        if living_area_sqft:
                            logger.info(f"✅ Square footage extracted: {living_area_sqft:,} sqft")
                        else:
                            logger.warning(f"⚠️  Square footage NOT found for property: {property_data.get('address')}")
                        
                        # ✅ Extract property images
                        property_data['image_url'] = self._extract_property_image()
                        if property_data.get('image_url'):
                            logger.info(f"✅ Property image extracted")
                        
                        # ✅ Extract additional details
                        property_data['days_on_market'] = prop_json.get('daysOnZillow')
                        
                        return property_data
                
                except:
                    pass
                
                try:
                    property_data['address'] = self._safe_extract(By.CSS_SELECTOR, 'h1', 'text')
                    property_data['price'] = self._safe_extract(By.CSS_SELECTOR, '[data-testid="price-header"]', 'text')
                    
                    if property_data.get('address'):
                        return property_data
                
                except:
                    pass
            
            except Exception as e:
                logger.error(f"Error extracting property: {str(e)[:50]}")
        
        logger.warning(f"Failed to extract property: {property_url}")
        return None
    
    def _safe_extract(self, by: By, selector: str, attribute: str = 'text') -> Optional[str]:
        """Safely extract element"""
        try:
            element = self.driver.find_element(by, selector)
            return element.text if attribute == 'text' else element.get_attribute(attribute)
        except:
            return None
    
    def _extract_property_image(self) -> Optional[str]:
        """
        Extract the first/hero image from Zillow property detail page
        
        Returns:
            Image URL string or None if not found
        """
        try:
            # Try multiple selectors for images on Zillow
            image_selectors = [
                'img[alt*="photo"]',
                'img[alt*="Photo"]',
                'img[data-testid*="image"]',
                'picture img',
                'img.hdp-photo',
                'img[class*="photo"]'
            ]
            
            for selector in image_selectors:
                try:
                    images = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if images:
                        # Get the first image with a valid src
                        for img in images:
                            src = img.get_attribute('src')
                            if src and ('zillow' in src or 'amazonaws' in src or 'http' in src):
                                logger.debug(f"✓ Found image: {src[:50]}...")
                                return src
                except:
                    continue
            
            # Fallback: Try to find any image with large src
            try:
                all_images = self.driver.find_elements(By.TAG_NAME, 'img')
                for img in all_images:
                    src = img.get_attribute('src')
                    if src and len(src) > 50 and ('zillow' in src or 'amazonaws' in src):
                        logger.debug(f"✓ Found image (fallback): {src[:50]}...")
                        return src
            except:
                pass
            
            logger.debug("⚠️  No image found for this property")
            return None
            
        except Exception as e:
            logger.debug(f"Image extraction error: {str(e)[:50]}")
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