import pyzill
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import time
import json
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import logging

# Configure logging to reduce noise
logging.getLogger("geopy").setLevel(logging.WARNING)


class ZillowScraperAgent:
    """
    Scrapes Zillow for all discovered ZIP codes using dynamic geocoding
    Returns structured JSON with sold homes and for-sale listings
    """
    
    def __init__(self):
        self.max_retries = 3
        self.retry_delay = 5
        self.geocoder = Nominatim(user_agent="realestate-valuation-bot")
        self.zip_cache = {}  # Cache coordinates to avoid repeated API calls

    def _get_zip_coordinates(self, zip_code: str) -> Optional[Tuple[float, float, float, float]]:
        """
        Get bounding box coordinates for a ZIP code using geocoding
        Returns (sw_lat, sw_long, ne_lat, ne_long) or None if failed
        """
        # Check cache first
        if zip_code in self.zip_cache:
            return self.zip_cache[zip_code]
        
        try:
            print(f"   📍 Geocoding ZIP {zip_code}...")
            
            # Geocode the ZIP code
            location = self.geocoder.geocode(f"{zip_code}, USA", timeout=10)
            
            if not location:
                print(f"   ❌ Could not geocode ZIP {zip_code}")
                return None
            
            # Get the bounding box
            if hasattr(location, 'raw') and 'boundingbox' in location.raw:
                bbox = location.raw['boundingbox']
                # OSM returns [south, north, west, east]
                south, north, west, east = map(float, bbox)
                
                # Return as (sw_lat, sw_long, ne_lat, ne_long)
                coords = (south, west, north, east)
                
                # Cache the result
                self.zip_cache[zip_code] = coords
                print(f"   ✅ Got coordinates: {coords}")
                return coords
            else:
                # Fallback: create a small bounding box around the point
                lat, lon = location.latitude, location.longitude
                margin = 0.05  # Roughly 3-4 miles
                coords = (lat - margin, lon - margin, lat + margin, lon + margin)
                
                # Cache the result
                self.zip_cache[zip_code] = coords
                print(f"   ✅ Got point coordinates (with margin): {coords}")
                return coords
                
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            print(f"   ❌ Geocoding service error for {zip_code}: {str(e)}")
            time.sleep(2)  # Brief delay before retrying
            return None
        except Exception as e:
            print(f"   ❌ Geocoding error for {zip_code}: {str(e)}")
            return None
    
    def scrape_all_zips(self, zip_data: Dict, timeframe_months: int = 6, target_property: Dict = None) -> Dict:
        """
        Scrape all ZIP codes for sold and for-sale homes
        
        Args:
            zip_data: Output from ZipDiscoveryAgent with all_zips list
            timeframe_months: How many months back to get sold homes
        
        Returns:
            JSON with all scraped property data
        """
        
        print(f"\n{'='*80}")
        print(f"🕷️  AGENT 3: Zillow Multi-ZIP Scraper")
        print(f"{'='*80}\n")
        
        all_zips = zip_data['all_zips']
        primary_zip = zip_data['primary_zip']
        
        # Get asking price from target property
        asking_price = None
        if target_property and 'asking_price' in target_property:
            asking_price = target_property['asking_price']
            print(f"💰 Using asking price: ${asking_price:,}")
        
        print(f"🎯 Target: {len(all_zips)} ZIP codes")
        print(f"📅 Timeframe: Last {timeframe_months} months")
        print(f"📍 ZIPs: {', '.join(all_zips)}\n")
        
        cutoff_date = datetime.now() - timedelta(days=timeframe_months * 30)
        
        all_sold_homes = []
        all_for_sale_homes = []
        scraping_stats = {
            'total_zips': len(all_zips),
            'successful_zips': 0,
            'failed_zips': 0,
            'total_sold': 0,
            'total_for_sale': 0
        }
        
        # Scrape each ZIP
        for i, zip_code in enumerate(all_zips, 1):
            print(f"[{i}/{len(all_zips)}] Scraping ZIP {zip_code}...")
            
            try:
                # Scrape sold homes
                sold = self._scrape_sold_homes(zip_code, cutoff_date, asking_price, target_property)
                all_sold_homes.extend(sold)
                
                # Scrape for-sale homes
                for_sale = self._scrape_for_sale_homes(zip_code, asking_price, target_property)
                all_for_sale_homes.extend(for_sale)
                
                print(f"   ✅ Sold: {len(sold)} | For Sale: {len(for_sale)}")
                
                scraping_stats['successful_zips'] += 1
                scraping_stats['total_sold'] += len(sold)
                scraping_stats['total_for_sale'] += len(for_sale)
                
                # Rate limiting - be nice to Zillow
                time.sleep(3)
                
            except Exception as e:
                print(f"   ❌ Failed: {str(e)}")
                scraping_stats['failed_zips'] += 1
                continue
        
        print(f"\n{'='*60}")
        print(f"📊 SCRAPING COMPLETE:")
        print(f"   • Total Sold Homes: {scraping_stats['total_sold']}")
        print(f"   • Total For Sale: {scraping_stats['total_for_sale']}")
        print(f"   • Successful ZIPs: {scraping_stats['successful_zips']}/{scraping_stats['total_zips']}")
        print(f"{'='*60}\n")
        
        # Return pure JSON
        return {
            "primary_zip": primary_zip,
            "all_zips_scraped": all_zips,
            "sold_homes": all_sold_homes,
            "for_sale_homes": all_for_sale_homes,
            "scraping_stats": scraping_stats,
            "collection_timestamp": datetime.now().isoformat(),
            "timeframe_months": timeframe_months
        }
    
    def _scrape_sold_homes(self, zip_code: str, cutoff_date: datetime, asking_price: int = None, target_property: Dict = None) -> List[Dict]:
        """Scrape sold homes for a single ZIP using geocoded coordinates"""
        
        # Get coordinates for this ZIP code
        coords = self._get_zip_coordinates(zip_code)
        if not coords:
            print(f"   ❌ Cannot scrape {zip_code} - no coordinates")
            return []
        
        sw_lat, sw_long, ne_lat, ne_long = coords
        
        # For search_value, use a city name instead of empty string for sold properties
        search_value = "Austin"  # Use city name for better sold results
        
        # Get property filters from target_property
        min_beds = target_property.get('bedrooms') - 1 if target_property and target_property.get('bedrooms') else None
        max_beds = target_property.get('bedrooms') + 1 if target_property and target_property.get('bedrooms') else None
        min_baths = target_property.get('bathrooms') - 1 if target_property and target_property.get('bathrooms') else None
        max_baths = target_property.get('bathrooms') + 1 if target_property and target_property.get('bathrooms') else None
        
        # Set price range for sold properties (help filter relevant results)
        min_price = 100000  # Minimum $100k to filter out unrealistic low prices
        max_price = 2000000  # Maximum $2M to focus on typical residential market
        
        for attempt in range(self.max_retries):
            try:
                print(f"   🔍 Attempt {attempt + 1}: Scraping sold homes...")
                # Parse proxy - for now using None but should be configured for production
                proxy_url = None  # pyzill.parse_proxy("proxy_ip", "proxy_port", "username", "password")
                
                # Use correct pyzill parameter order: pagination comes first
                # Use smaller zoom_value for sold (as per documentation example)
                results = pyzill.sold(
                    1,  # pagination - first parameter
                    search_value=search_value,
                    min_beds=min_beds,
                    max_beds=max_beds,
                    min_bathrooms=min_baths,
                    max_bathrooms=max_baths,
                    min_price=min_price,
                    max_price=max_price,
                    ne_lat=ne_lat,
                    ne_long=ne_long,
                    sw_lat=sw_lat,
                    sw_long=sw_long,
                    zoom_value=8,  # Smaller zoom for sold properties (documentation uses 5)
                    proxy_url=proxy_url
                )
                
                return self._parse_sold_results(results, cutoff_date, zip_code)
                
            except Exception as e:
                print(f"   ❌ Attempt {attempt + 1} failed: {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    print(f"   ❌ All attempts failed for sold homes in {zip_code}")
                    return []
        
        return []
    
    def _scrape_for_sale_homes(self, zip_code: str, asking_price: int = None, target_property: Dict = None) -> List[Dict]:
        """Scrape for-sale homes for a single ZIP using geocoded coordinates"""
        
        # Get coordinates for this ZIP code
        coords = self._get_zip_coordinates(zip_code)
        if not coords:
            print(f"   ❌ Cannot scrape {zip_code} - no coordinates")
            return []
        
        sw_lat, sw_long, ne_lat, ne_long = coords
        
        # For search_value, use empty string (let coordinates do the work)
        search_value = ""  # Empty string lets the coordinates define the search area
        
        # Get property filters from target_property
        min_beds = target_property.get('bedrooms') - 1 if target_property and target_property.get('bedrooms') else None
        max_beds = target_property.get('bedrooms') + 1 if target_property and target_property.get('bedrooms') else None
        min_baths = target_property.get('bathrooms') - 1 if target_property and target_property.get('bathrooms') else None
        max_baths = target_property.get('bathrooms') + 1 if target_property and target_property.get('bathrooms') else None
        
        for attempt in range(self.max_retries):
            try:
                print(f"   🏠 Attempt {attempt + 1}: Scraping for-sale homes...")
                # Parse proxy - for now using None but should be configured for production
                proxy_url = None  # pyzill.parse_proxy("proxy_ip", "proxy_port", "username", "password")
                
                # Use correct pyzill parameter order: pagination comes first
                results = pyzill.for_sale(
                    1,  # pagination - first parameter
                    search_value=search_value,
                    min_beds=min_beds,
                    max_beds=max_beds,
                    min_bathrooms=min_baths,
                    max_bathrooms=max_baths,
                    min_price=None,
                    max_price=None,
                    ne_lat=ne_lat,
                    ne_long=ne_long,
                    sw_lat=sw_lat,
                    sw_long=sw_long,
                    zoom_value=12,
                    proxy_url=proxy_url
                )
                
                return self._parse_for_sale_results(results, zip_code)
                
            except Exception as e:
                print(f"   ❌ Attempt {attempt + 1} failed: {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    print(f"   ❌ All attempts failed for for-sale homes in {zip_code}")
                    return []
        
        return []
    
    def _parse_sold_results(self, results: Dict, cutoff_date: datetime, zip_code: str) -> List[Dict]:
        """Parse PyZill sold results into clean JSON"""
        
        properties = []
        
        try:
            # New API structure - check listResults first, then mapResults as fallback
            listings = []
            if 'listResults' in results and results['listResults']:
                listings = results['listResults']
            elif 'mapResults' in results and results['mapResults']:
                listings = results['mapResults']
            
            # Debug: show count of listings found
            print(f"   🔍 Processing {len(listings)} sold listings from API")
            
            for listing in listings:
                try:
                    # Check if it's actually a sold property
                    status_text = listing.get('statusText', '').upper()
                    raw_status = listing.get('rawHomeStatusCd', '').upper()
                    
                    # Skip if not actually sold
                    if 'FOR SALE' in status_text or 'FOR_SALE' in raw_status:
                        continue
                    
                    # Accept properties marked as "SOLD", "CLOSED", or "RECENTLYSOLD"
                    if not any(status in raw_status for status in ['SOLD', 'CLOSED', 'RECENTLY']):
                        continue
                    
                    # For sold properties, skip date filtering if no date is available
                    # Most recent sales won't have exact sale dates in the API
                    date_sold = None
                    date_sold_str = "Recent"  # Default for recent sales
                    date_sold_ms = listing.get('dateSold')
                    
                    # Try to find a date field
                    if date_sold_ms:
                        date_sold = datetime.fromtimestamp(date_sold_ms / 1000)
                        if date_sold < cutoff_date:
                            continue
                        date_sold_str = date_sold.isoformat()
                    
                    # Build clean property JSON using soldPrice for sold properties
                    prop = {
                        "zpid": listing.get('zpid'),
                        "address": listing.get('address'),
                        "city": listing.get('addressCity'),
                        "state": listing.get('addressState'),
                        "zipcode": listing.get('addressZipcode', zip_code),
                        "price": listing.get('soldPrice') or listing.get('price'),  # Use soldPrice for sold properties
                        "bedrooms": listing.get('beds'),  # Note: 'beds' not 'bedrooms'
                        "bathrooms": listing.get('baths'),  # Note: 'baths' not 'bathrooms'
                        "living_area_sqft": listing.get('area'),
                        "lot_area_sqft": listing.get('lotAreaValue'),
                        "year_built": listing.get('yearBuilt'),
                        "date_sold": date_sold_str,
                        "days_on_zillow": listing.get('daysOnZillow'),
                        "property_type": listing.get('hdpData', {}).get('homeInfo', {}).get('homeType'),
                        "listing_type": "SOLD",
                        "status": listing.get('statusText'),
                        "raw_status": listing.get('rawHomeStatusCd'),
                        "latitude": listing.get('latLong', {}).get('latitude') if listing.get('latLong') else None,
                        "longitude": listing.get('latLong', {}).get('longitude') if listing.get('latLong') else None,
                        "url": f"https://www.zillow.com{listing.get('detailUrl', '')}"
                    }
                    
                    # Ensure numeric fields are properly converted
                    # Convert price to integer if it's a string
                    if prop['price'] and isinstance(prop['price'], str):
                        try:
                            # Remove dollar signs, commas, and convert to int
                            prop['price'] = int(prop['price'].replace('$', '').replace(',', ''))
                        except (ValueError, AttributeError):
                            prop['price'] = None
                    
                    # Convert numeric fields to proper types
                    for field in ['bedrooms', 'bathrooms', 'living_area_sqft', 'lot_area_sqft', 'year_built', 'days_on_zillow']:
                        if prop[field] and isinstance(prop[field], str):
                            try:
                                if field == 'bathrooms':
                                    prop[field] = float(prop[field])  # Bathrooms can be float (e.g., 1.5)
                                else:
                                    prop[field] = int(prop[field].replace(',', ''))
                            except (ValueError, AttributeError):
                                prop[field] = None
                    
                    # Calculate price per sqft if possible
                    try:
                        price = prop['price']
                        area = prop['living_area_sqft']
                        if price and area and isinstance(price, (int, float)) and isinstance(area, (int, float)):
                            prop['price_per_sqft'] = round(price / area, 2)
                        else:
                            prop['price_per_sqft'] = None
                    except (ValueError, ZeroDivisionError, TypeError):
                        prop['price_per_sqft'] = None
                    
                    properties.append(prop)
                    
                except Exception as e:
                    print(f"   ❌ Error parsing listing: {str(e)}")
                    continue
                    
        except Exception as e:
            print(f"   ❌ Error parsing results: {str(e)}")
            pass
        
        return properties
    
    def _parse_for_sale_results(self, results: Dict, zip_code: str) -> List[Dict]:
        """Parse PyZill for-sale results into clean JSON"""
        
        properties = []
        
        try:
            # New API structure - check listResults first, then mapResults as fallback
            listings = []
            if 'listResults' in results and results['listResults']:
                listings = results['listResults']
            elif 'mapResults' in results and results['mapResults']:
                listings = results['mapResults']
            
            print(f"   🏠 Processing {len(listings)} for-sale listings from API")
            
            for listing in listings:
                try:
                    prop = {
                        "zpid": listing.get('zpid'),
                        "address": listing.get('address'),
                        "city": listing.get('addressCity'),
                        "state": listing.get('addressState'),
                        "zipcode": listing.get('addressZipcode', zip_code),
                        "price": listing.get('price'),
                        "bedrooms": listing.get('beds'),  # Use 'beds' not 'bedrooms' for consistency
                        "bathrooms": listing.get('baths'),  # Use 'baths' not 'bathrooms' for consistency
                        "living_area_sqft": listing.get('area'),
                        "lot_area_sqft": listing.get('lotAreaValue'),
                        "year_built": listing.get('yearBuilt'),
                        "days_on_zillow": listing.get('daysOnZillow'),
                        "property_type": listing.get('hdpData', {}).get('homeInfo', {}).get('homeType'),
                        "listing_type": "FOR_SALE",
                        "status": listing.get('statusText'),
                        "latitude": listing.get('latLong', {}).get('latitude') if listing.get('latLong') else None,
                        "longitude": listing.get('latLong', {}).get('longitude') if listing.get('latLong') else None,
                        "url": f"https://www.zillow.com{listing.get('detailUrl', '')}"
                    }
                    
                    # Ensure numeric fields are properly converted
                    # Convert price to integer if it's a string
                    if prop['price'] and isinstance(prop['price'], str):
                        try:
                            # Remove dollar signs, commas, and convert to int
                            prop['price'] = int(prop['price'].replace('$', '').replace(',', ''))
                        except (ValueError, AttributeError):
                            prop['price'] = None
                    
                    # Convert numeric fields to proper types
                    for field in ['bedrooms', 'bathrooms', 'living_area_sqft', 'lot_area_sqft', 'year_built', 'days_on_zillow']:
                        if prop[field] and isinstance(prop[field], str):
                            try:
                                if field == 'bathrooms':
                                    prop[field] = float(prop[field])  # Bathrooms can be float (e.g., 1.5)
                                else:
                                    prop[field] = int(prop[field].replace(',', ''))
                            except (ValueError, AttributeError):
                                prop[field] = None
                    
                    # Calculate price per sqft if possible
                    try:
                        price = prop['price']
                        area = prop['living_area_sqft']
                        if price and area and isinstance(price, (int, float)) and isinstance(area, (int, float)):
                            prop['price_per_sqft'] = round(price / area, 2)
                        else:
                            prop['price_per_sqft'] = None
                    except (ValueError, ZeroDivisionError, TypeError):
                        prop['price_per_sqft'] = None
                    
                    properties.append(prop)
                    
                except Exception as e:
                    print(f"   ❌ Error parsing listing: {str(e)}")
                    continue
                    
        except Exception as e:
            print(f"   ❌ Error parsing results: {str(e)}")
            pass
        
        return properties