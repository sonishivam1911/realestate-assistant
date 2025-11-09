from bs4 import BeautifulSoup
import re
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor
import requests

class HTMLParser:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def extract_price(self, text: str) -> Optional[float]:
        """Extract price from text - must have clear real estate context"""
        # Look for prices with strong real estate keywords and context
        strong_patterns = [
            # "median price is $769,000"
            r'(?:median|average|typical)\s+(?:price|listing price)[:\s]+\$?([\d,]+)',
            # "sold for $759,000, down"
            r'(?:sold\s+for|price\s+of|listed\s+at|asking)[:\s]+\$?([\d,]+)(?=\s*[,.])',
            # Price with context like "$759,000, down X%" 
            r'\$[\d,]+(?=\s*,\s*(?:down|compared))',
        ]
        
        for pattern in strong_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # Extract the price value
                if match.lastindex:
                    price_str = match.group(1)
                else:
                    price_str = match.group()
                    # Extract numbers from the group
                    price_str = re.sub(r'[^\d]', '', price_str)
                
                # Clean up
                price_str = str(price_str).replace(',', '')
                
                try:
                    price_val = float(price_str)
                    # Only accept reasonable home prices
                    # Filter out anything under 50k (likely not a home) or over 10M
                    if 50000 <= price_val <= 10000000:
                        return price_val
                except (ValueError, IndexError):
                    continue
        
        return None
    
    def extract_sqft(self, text: str) -> Optional[int]:
        """Extract square footage from text"""
        patterns = [
            # Context-aware patterns for real estate
            r'(?:property|home|house|building).*?([\d,]+)\s*(?:sq\.?\s*ft|square feet|sqft)',
            r'(?:sq\.?\s*ft|square feet|sqft)[:\s]+([\d,]+)',
            r'([\d,]+)\s*(?:sq\.?\s*ft|square feet|sqft)',
            r'([\d,]+)\s*sf\b',
            # Filter out very small numbers that might be addresses or dates
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    sqft_val = int(match.group(1).replace(',', ''))
                    # Filter unrealistic sqft values (400-15000 for residential)
                    if 400 <= sqft_val <= 15000:
                        return sqft_val
                except (ValueError, IndexError):
                    continue
        
        return None
    
    def extract_bedrooms(self, text: str) -> Optional[int]:
        """Extract bedroom count from text"""
        # Look for bedroom mentions in context
        patterns = [
            r'(\d+)\s*(?:bedrooms?|bds?|br)\b',  # "3 bedrooms" or "3br"
            r'(?:bedrooms?|bds?|br)[:\s]+(\d+)',  # "bedrooms: 3"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    bedrooms = int(match.group(1))
                    # Filter unrealistic bedroom counts
                    if 1 <= bedrooms <= 10:
                        return bedrooms
                except (ValueError, IndexError):
                    continue
        
        return None
    
    def extract_date(self, text: str) -> Optional[str]:
        """Extract date from text"""
        # Look for dates like "Oct 2024", "October 15, 2024", "10/15/2024"
        patterns = [
            r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}',
            r'\d{1,2}/\d{1,2}/\d{4}',
            r'\d{4}-\d{2}-\d{2}'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group()
        
        return None
    
    def parse_search_result(self, result: Dict) -> Dict:
        """Parse a single search result"""
        title = result.get('title', '')
        body = result.get('body', '')
        url = result.get('href', '')
        
        combined_text = f"{title} {body}"
        
        parsed = {
            "url": url,
            "title": title,
            "snippet": body,
            "extracted_data": {
                "price": self.extract_price(combined_text),
                "sqft": self.extract_sqft(combined_text),
                "bedrooms": self.extract_bedrooms(combined_text),
                "date": self.extract_date(combined_text)
            }
        }
        
        return parsed
    
    def parse_all_results(self, search_results: Dict[str, str]) -> Dict:
        """Parse all search results from DuckDuckGo"""
        parsed_results = {}
        all_results = []
        
        for query, result_text in search_results.items():
            print(f"\n📄 Parsing query: {query[:60]}")
            print(f"   Result length: {len(str(result_text))} characters")
            
            if not result_text:
                parsed_results[query] = []
                continue
            
            # Parse the text result
            parsed = self.parse_search_result_text(str(result_text))
            parsed_results[query] = parsed
            
            if parsed['extracted_data']:
                all_results.append(parsed)
                print(f"   ✓ Extracted: {parsed['extracted_data']}")
            else:
                print(f"   ⚠️  No data extracted")
        
        # Group results by type
        comparable_sales = []
        market_data = []
        
        for result in all_results:
            data = result['extracted_data']
            # If has price and sqft, likely a comp
            if data.get('price') and data.get('sqft'):
                comparable_sales.append({
                    "title": result['title'],
                    "price": data['price'],
                    "sqft": data['sqft'],
                    "bedrooms": data.get('bedrooms'),
                    "date": data.get('date'),
                    "price_per_sqft": data['price'] / data['sqft'] if data['sqft'] else None
                })
            elif data.get('price'):
                market_data.append(result)
        
        return {
            "comparable_sales": comparable_sales,
            "market_data": market_data,
            "all_parsed_results": parsed_results,
            "summary": {
                "total_comps_found": len(comparable_sales),
                "total_market_data": len(market_data)
            }
        }
    
    def parse_search_result_text(self, text: str) -> Dict:
        """Parse a text search result from DuckDuckGo"""
        extracted_data = {
            "price": self.extract_price(text),
            "sqft": self.extract_sqft(text),
            "bedrooms": self.extract_bedrooms(text),
            "date": self.extract_date(text)
        }
        
        return {
            "title": text[:100],
            "snippet": text,
            "extracted_data": extracted_data
        }