"""
Zillow Filter URL Capture Tool
Author: Built for Shivam's Real Estate AI Agent

Purpose: Capture Zillow search URLs with your desired filters applied
This tool lets you manually set filters in the browser, then captures the URL
for use in automated scraping.

Usage:
1. Run this script
2. Browser opens to your base search location
3. Manually click filters (Sold, Property Type, Beds/Baths, etc.)
4. Press Enter in terminal when done
5. Script captures and saves the URL
"""

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
from pathlib import Path
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ZillowFilterCapture:
    """
    Tool to capture Zillow search URLs with filters applied
    """
    
    def __init__(self):
        self.driver = None
        self.captured_urls = []
        self.config_dir = Path('zillow_configs')
        self.config_dir.mkdir(exist_ok=True)
    
    def init_driver(self):
        """Initialize Chrome driver"""
        try:
            options = uc.ChromeOptions()
            
            # Keep it visible so user can interact
            options.add_argument('--start-maximized')
            options.add_argument('--disable-blink-features=AutomationControlled')
            
            self.driver = uc.Chrome(options=options, use_subprocess=False)
            self.driver.set_page_load_timeout(120)
            
            logger.info("✓ Chrome driver initialized")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize driver: {e}")
            return False
    
    def _build_url_with_filters(self, base_location: str, filters: dict = None) -> str:
        """
        Build Zillow URL with filters applied (for auto-mode)
        
        Args:
            base_location: Base location (ZIP or city)
            filters: Dict with bedrooms, bathrooms, property_type, etc.
        
        Returns:
            Built URL with filters
        """
        import urllib.parse
        
        if not filters:
            filters = {}
        
        # Build searchQueryState
        search_state = {
            "pagination": {},
            "isMapVisible": True,
            "filterState": {}
        }
        
        # Property type filters
        property_type = filters.get('property_type')
        if property_type:
            type_map = {
                "houses": "sf",
                "single_family": "sf",
                "townhouse": "tow",
                "townhomes": "tow",
                "condo": "con",
                "condos": "con",
                "apartment": "apco",
                "apartments": "apco",
                "multi_family": "mf",
                "land": "land",
                "manufactured": "manu"
            }
            
            all_types = ["sf", "mf", "con", "apco", "land", "tow", "manu"]
            for ptype in all_types:
                search_state["filterState"][ptype] = {"value": False}
            
            ptype_lower = property_type.lower()
            if ptype_lower in type_map:
                zillow_code = type_map[ptype_lower]
                search_state["filterState"][zillow_code] = {"value": True}
        
        # Bedroom filter
        if filters.get('bedrooms'):
            search_state["filterState"]["beds"] = {"min": filters['bedrooms']}
        
        # Bathroom filter
        if filters.get('bathrooms'):
            search_state["filterState"]["baths"] = {"min": filters['bathrooms']}
        
        # Price filters
        if filters.get('min_price') or filters.get('max_price'):
            search_state["filterState"]["price"] = {}
            if filters.get('min_price'):
                search_state["filterState"]["price"]["min"] = filters['min_price']
            if filters.get('max_price'):
                search_state["filterState"]["price"]["max"] = filters['max_price']
        
        # Square footage
        if filters.get('min_sqft') or filters.get('max_sqft'):
            search_state["filterState"]["sqft"] = {}
            if filters.get('min_sqft'):
                search_state["filterState"]["sqft"]["min"] = filters['min_sqft']
            if filters.get('max_sqft'):
                search_state["filterState"]["sqft"]["max"] = filters['max_sqft']
        
        # Status filter
        status = filters.get('status', 'for_sale')
        if status == "sold":
            search_state["filterState"]["rs"] = {"value": True}
        
        # Convert to JSON and URL encode
        json_str = json.dumps(search_state, separators=(',', ':'))
        encoded = urllib.parse.quote(json_str)
        
        url = f"https://www.zillow.com/{base_location}/?searchQueryState={encoded}"
        return url
    
    def _validate_url_location(self, url: str, expected_location: str) -> bool:
        """
        Validate that the URL contains the expected location
        
        Args:
            url: The captured Zillow URL
            expected_location: The expected location (ZIP or city name)
        
        Returns:
            True if location matches, False otherwise
        """
        try:
            # Extract the location from URL (comes right after /zillow.com/)
            # Examples: https://www.zillow.com/08873/?... or https://www.zillow.com/jersey-city-nj/?...
            
            import re
            
            # Pattern to extract location from URL
            match = re.search(r'zillow\.com/([^/?]+)', url)
            if match:
                url_location = match.group(1)
                
                # For ZIP codes, do exact match
                if expected_location.isdigit():
                    return url_location == expected_location
                else:
                    # For city names, do case-insensitive comparison
                    return url_location.lower() == expected_location.lower()
        except Exception as e:
            logger.debug(f"Error validating URL location: {e}")
        
        return False
    
    def _extract_and_display_filters(self, url: str):
        """
        Extract the searchQueryState from URL and display it in human-readable format
        This helps users verify they captured the right filters
        
        Args:
            url: Zillow URL with searchQueryState parameter
        """
        try:
            import urllib.parse
            
            # Parse URL
            parsed = urllib.parse.urlparse(url)
            params = urllib.parse.parse_qs(parsed.query)
            
            if 'searchQueryState' in params:
                search_state_str = params['searchQueryState'][0]
                # URL decode
                decoded = urllib.parse.unquote(search_state_str)
                search_state = json.loads(decoded)
                
                filter_state = search_state.get('filterState', {})
                
                if filter_state:
                    print("\n📋 CAPTURED FILTERS SUMMARY:")
                    print("-" * 60)
                    
                    # Property type filters
                    prop_types = {
                        'sf': 'Houses (Single Family)',
                        'tow': 'Townhomes',
                        'con': 'Condos',
                        'apco': 'Apartments',
                        'mf': 'Multi-Family',
                        'manu': 'Manufactured',
                        'land': 'Land'
                    }
                    
                    print("\n🏠 Property Types:")
                    found_types = False
                    for code, name in prop_types.items():
                        if code in filter_state and filter_state[code].get('value') == True:
                            print(f"   ✓ {name}")
                            found_types = True
                    if not found_types:
                        print("   (All property types)")
                    
                    # Beds/Baths
                    if 'beds' in filter_state:
                        min_beds = filter_state['beds'].get('min')
                        max_beds = filter_state['beds'].get('max')
                        if min_beds or max_beds:
                            print(f"\n🛏️  Bedrooms: min={min_beds}, max={max_beds}")
                    
                    if 'baths' in filter_state:
                        min_baths = filter_state['baths'].get('min')
                        max_baths = filter_state['baths'].get('max')
                        if min_baths or max_baths:
                            print(f"🚿 Bathrooms: min={min_baths}, max={max_baths}")
                    
                    # Price range
                    if 'price' in filter_state:
                        min_price = filter_state['price'].get('min')
                        max_price = filter_state['price'].get('max')
                        if min_price or max_price:
                            print(f"💰 Price: ${min_price or '0'}k - ${max_price or 'unlimited'}k")
                    
                    # Square footage
                    if 'sqft' in filter_state:
                        min_sqft = filter_state['sqft'].get('min')
                        max_sqft = filter_state['sqft'].get('max')
                        if min_sqft or max_sqft:
                            print(f"📐 Square Footage: {min_sqft or '0'} - {max_sqft or 'unlimited'} sqft")
                    
                    # Year built
                    if 'year' in filter_state:
                        min_year = filter_state['year'].get('min')
                        max_year = filter_state['year'].get('max')
                        if min_year or max_year:
                            print(f"📅 Year Built: {min_year or 'any'} - {max_year or 'any'}")
                    
                    # Status (Sold/For Sale)
                    if 'rs' in filter_state and filter_state['rs'].get('value') == True:
                        print(f"📌 Status: SOLD")
                    
                    print("-" * 60)
                    
        except Exception as e:
            logger.debug(f"Error extracting filters: {e}")
    
    def wait_for_user_input(self, message: str):
        """Wait for user to press Enter"""
        print("\n" + "="*80)
        print(message)
        print("="*80)
        input("\nPress Enter when ready...")
    
    def capture_filter_url(self, base_location: str, filter_name: str, filters: dict = None, auto_mode: bool = False):
        """
        Capture a filtered search URL
        
        Args:
            base_location: Base search (e.g., "monroe-township-nj", "08873")
            filter_name: Descriptive name for this filter config
            filters: Optional filters dict for auto mode (bedrooms, bathrooms, property_type, etc.)
            auto_mode: If True, build URL programmatically without user interaction (no browser needed)
        """
        try:
            # If auto_mode, build URL programmatically without opening browser
            if auto_mode:
                built_url = self._build_url_with_filters(base_location, filters)
                
                # Save this auto-generated config to master list
                config = {
                    'filter_name': filter_name,
                    'base_location': base_location,
                    'captured_url': built_url,
                    'captured_at': datetime.now().isoformat(),
                    'notes': 'URL auto-generated from filter params'
                }
                
                master_file = self.config_dir / 'all_filter_urls.json'
                
                if master_file.exists():
                    with open(master_file, 'r') as f:
                        all_configs = json.load(f)
                else:
                    all_configs = []
                
                all_configs.append(config)
                
                with open(master_file, 'w') as f:
                    json.dump(all_configs, f, indent=2)
                
                logger.info(f"✓ Auto-generated config saved for {filter_name}")
                return built_url
            
            # Manual mode: Open browser and wait for user to set filters
            # Build base URL
            base_url = f"https://www.zillow.com/{base_location}/"
            
            logger.info(f"Opening Zillow: {base_url}")
            self.driver.get(base_url)
            
            # Initial wait for page load
            time.sleep(8)
            
            print("\n" + "🎯 "+"="*76)
            print("  ZILLOW FILTER SETUP - FOLLOW THESE STEPS:")
            print("="*80)
            print("\n  1. ✋ Wait for the page to fully load")
            print("  2. 🖱️  Click on the filters you want:")
            print("     - For sale / For rent / Sold")
            print("     - Property type (Houses, Townhomes, etc.)")
            print("     - Beds & baths")
            print("     - Price range")
            print("     - Any other filters you need")
            print("  3. ⏳ Wait for results to load after each filter")
            print("  4. ✅ When completely done, come back here and press Enter")
            print("\n" + "="*80)
            
            input("\nPress Enter after you've finished setting all filters...")
            
            # Capture the current URL
            current_url = self.driver.current_url
            
            # Clean up the URL (remove unnecessary tracking params)
            cleaned_url = current_url.split('#')[0]  # Remove hash
            
            # CRITICAL: Validate that the captured URL matches the base_location
            # This prevents accidentally scraping the wrong location
            url_location_match = self._validate_url_location(cleaned_url, base_location)
            
            print("\n" + "="*80)
            print("✓ URL CAPTURED!")
            print("="*80)
            print(f"\nFull URL:\n{cleaned_url}")
            
            # Extract and display the filter state for verification
            if 'searchQueryState' in cleaned_url:
                print("\n✓ Filter parameters detected in URL")
                # Show human-readable summary of filters
                self._extract_and_display_filters(cleaned_url)
            else:
                print("\n⚠️  Warning: No filter parameters detected. Did filters apply?")
            
            # Check if URL location matches base_location
            if not url_location_match:
                print("\n" + "⚠️ "*40)
                print("⚠️  LOCATION MISMATCH WARNING!")
                print("⚠️ "*40)
                print(f"\n⚠️  Expected location in URL: {base_location}")
                print(f"⚠️  URL contains different location!")
                print(f"\n⚠️  This could cause scraping the WRONG AREA!")
                print(f"\n⚠️  Current URL: {cleaned_url[:80]}...")
                
                verify = input("\n⚠️  Continue anyway? (yes/no): ").strip().lower()
                if verify != 'yes':
                    print("❌ Capture cancelled.")
                    return None
            
            # Save the configuration
            config = {
                'filter_name': filter_name,
                'base_location': base_location,
                'captured_url': cleaned_url,
                'captured_at': datetime.now().isoformat(),
                'notes': 'URL captured via manual filter selection'
            }
            
            # Save to JSON file
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            config_file = self.config_dir / f'{filter_name}_{timestamp}.json'
            
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            print(f"\n✓ Configuration saved to: {config_file}")
            
            # Also append to a master list
            master_file = self.config_dir / 'all_filter_urls.json'
            
            if master_file.exists():
                with open(master_file, 'r') as f:
                    all_configs = json.load(f)
            else:
                all_configs = []
            
            all_configs.append(config)
            
            with open(master_file, 'w') as f:
                json.dump(all_configs, f, indent=2)
            
            print(f"✓ Also saved to master list: {master_file}")
            
            return cleaned_url
            
        except Exception as e:
            logger.error(f"Error capturing filter URL: {e}")
            return None
    
    def capture_multiple_filters(self, base_location: str):
        """
        Capture multiple filter configurations in one session
        
        Args:
            base_location: Base search location
        """
        print("\n" + "🎯 "+"="*76)
        print("  MULTIPLE FILTER CAPTURE MODE")
        print("="*80)
        print("\n  You can capture multiple filter configurations in this session.")
        print("  For example:")
        print("    - 'sold_houses_3bed' - Sold houses with 3+ bedrooms")
        print("    - 'for_sale_under_500k' - Houses for sale under $500k")
        print("    - 'townhomes_2bed_2bath' - Townhomes with 2 bed, 2 bath")
        print("\n" + "="*80 + "\n")
        
        captured_count = 0
        
        while True:
            print(f"\n--- Filter Configuration #{captured_count + 1} ---")
            
            filter_name = input("\nEnter a name for this filter configuration (or 'done' to finish): ").strip()
            
            if filter_name.lower() == 'done':
                break
            
            if not filter_name:
                print("⚠️  Please provide a valid name")
                continue
            
            # Replace spaces with underscores
            filter_name = filter_name.replace(' ', '_')
            
            url = self.capture_filter_url(base_location, filter_name)
            
            if url:
                captured_count += 1
                print(f"\n✓ Filter '{filter_name}' captured successfully!")
            
            # Ask if they want to capture another
            if captured_count > 0:
                another = input("\nCapture another filter configuration? (yes/no): ").strip().lower()
                if another != 'yes':
                    break
        
        print("\n" + "="*80)
        print(f"✓ SESSION COMPLETE - Captured {captured_count} filter configurations")
        print("="*80)
        print(f"\nAll URLs saved in: {self.config_dir}/")
        print("You can now use these URLs in your scraper!")
    
    def load_saved_configs(self):
        """Load and display all saved filter configurations"""
        master_file = self.config_dir / 'all_filter_urls.json'
        
        if not master_file.exists():
            print("\nNo saved configurations found.")
            return
        
        with open(master_file, 'r') as f:
            configs = json.load(f)
        
        print("\n" + "="*80)
        print("📋 SAVED FILTER CONFIGURATIONS")
        print("="*80 + "\n")
        
        for idx, config in enumerate(configs, 1):
            print(f"{idx}. {config['filter_name']}")
            print(f"   Location: {config['base_location']}")
            print(f"   Captured: {config['captured_at']}")
            print(f"   URL: {config['captured_url'][:80]}...")
            print()
    
    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Browser closed")
            except Exception as e:
                logger.error(f"Error closing browser: {e}")


def main():
    """
    Main entry point
    """
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║        Zillow Filter URL Capture Tool                         ║
    ║                                                               ║
    ║  This tool helps you capture Zillow search URLs with your    ║
    ║  desired filters applied. You'll manually set filters in     ║
    ║  the browser, then we'll capture the URL for automated use.  ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)
    
    # Ask what they want to do
    print("\nWhat would you like to do?")
    print("1. Capture new filter URL(s)")
    print("2. View saved configurations")
    print("3. Both")
    
    choice = input("\nEnter your choice (1/2/3): ").strip()
    
    capturer = ZillowFilterCapture()
    
    try:
        if choice in ['2', '3']:
            capturer.load_saved_configs()
        
        if choice in ['1', '3']:
            # Get base location
            print("\n" + "="*80)
            base_location = input("Enter your search location (e.g., 'monroe-township-nj', '08873'): ").strip()
            
            if not base_location:
                print("⚠️  Location is required!")
                return
            
            # Initialize browser
            if not capturer.init_driver():
                print("❌ Failed to start browser")
                return
            
            # Start capture process
            capturer.capture_multiple_filters(base_location)
    
    finally:
        capturer.cleanup()
    
    print("\n" + "="*80)
    print("✓ All done! Use the captured URLs in your zillow_scraper.py")
    print("="*80)


if __name__ == "__main__":
    main()