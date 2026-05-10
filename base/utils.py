import time
import requests
from typing import Optional
from dataclasses import dataclass
from datetime import datetime
from functools import wraps
import re

@dataclass
class JobPosting:
    reference_id: str = ""
    apply_url: str = ""
    job_url: str = ""
    company_name: str = ""
    company_website: Optional[str] = ""
    company_logo_url: Optional[str] = ""
    job_title: str = ""
    job_type: Optional[str] = ""
    category: Optional[str] = ""
    city: Optional[str] = ""
    state: Optional[str] = ""
    country: Optional[str] = ""
    is_remote: str = ""
    salary_from: Optional[str] = ""
    salary_to: Optional[str] = ""
    salary_currency: Optional[str] = ""
    salary_period: Optional[str] = ""
    post_date: str = ""
    expiration_date: str = ""
    job_description: str = ""


class Get:

    @staticmethod
    def Session():
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        })
        return session

    @staticmethod
    def Json(url: str, session, retries: int = 3) -> Optional[dict | list]:
        for attempt in range(1, retries + 1):
            try:
                resp = session.get(url, timeout=20)
                if str(resp.status_code).startswith("2"):
                    return resp.json()
                if resp.status_code == 404:
                    print(f"    [404] {url}")
                    return None
                if resp.status_code == 429:
                    wait = 10 * attempt
                    print(f"    [429] Rate-limited, waiting {wait}s …")
                    time.sleep(wait)
                else:
                    print(f"    [HTTP {resp.status_code}] {url}")
                    time.sleep(2)
            except requests.RequestException as exc:
                print(f"    [ERROR] {exc}  (attempt {attempt}/{retries})")
                time.sleep(3 * attempt)
        return None

    @staticmethod
    def MdyDateStr(raw):
        if not raw:
            return ""
        for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d"):
            try:
                return datetime.strptime(raw[:26], fmt[:len(fmt)]).strftime("%m/%d/%Y")
            except ValueError:
                pass
        try:
            return datetime.fromisoformat(raw[:10]).strftime("%m/%d/%Y")
        except ValueError:
            return raw
        
    @staticmethod
    def ReferenceId(company, board, job_id, further_id = ''):
        if further_id:
            return f"{company}_{board}_{job_id}{further_id}".rstrip('_').lower()
        return f"{company}_{board}_{job_id}".rstrip('_').lower()
    
    @staticmethod
    def JobType(job_type_str):
        job_type_str = job_type_str.lower().strip().replace(" ", "")
        if "full" in job_type_str:
            return "full-time"
        if "part" in job_type_str:
            return "part-time"
        if "contract" in job_type_str or "freelance" in job_type_str:
            return "contract"
        return ""
    

def auto_map_countries(func):
    """Simpler decorator with fixed mapping"""
    country_mapping = {
        "USA": "United States",
        "U.S.A.": "United States",
        "US": "United States",
        "UK": "United Kingdom",
        "UAE": "United Arab Emirates",
        "UK&I": "United Kingdom & Ireland",
        "Korea, Republic of": "South Korea",
        "NORAM": "North America",
        "AMER": "Americas",
        "LATAM": "Latin America",
        "APAC": "Asia-Pacific",
        "DACH": "DACH Region",
        "LGC-AMERICAS": "Americas",
        "LCG-AMERICAS": "Americas",

        "EMEA": "Anywhere in EU",
        "Europe": "Anywhere in EU",
        "Global": "Anywhere in EU",
        "EU": "Anywhere in EU",
        "European Union": "Anywhere in EU"}
    
    regional_tags = ["EMEA", "Europe", "Global", "EU", "European Union", "Anywhere in EU"]

    eu_countries_list = [
    "Austria", "Belgium", "Bulgaria", "Croatia", "Cyprus", "Czech Republic",
    "Denmark", "Estonia", "Finland", "France", "Germany", "Greece", "Hungary",
    "Ireland", "Italy", "Latvia", "Lithuania", "Luxembourg", "Malta", "Netherlands",
    "Poland", "Portugal", "Romania", "Slovakia", "Slovenia", "Spain", "Sweden"]

    
    @wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        
        if not isinstance(result, list):
            return result
        
        # Step 1: Clean and map each location

        cleaned_results = []
        for item in result:
            country = item.get('country')
            country = "Anywhere in EU" if country.lower().strip() == 'remote' else country
            if country:
                country = re.sub(r'[-_\s]*remote[-_\s]*', ' ', country, flags=re.IGNORECASE)
                country = re.sub(r'[-_\s]*\(remote\)[-_\s]*', ' ', country, flags=re.IGNORECASE)
                country = country.replace('-', ' ').replace('_', ' ')
                country = ' '.join(country.split())
                country = country.strip()
                if country in country_mapping:
                    country = country_mapping[country]
            item['country'] = country
            cleaned_results.append(item)

        
        # Step 2: Collapse duplicate countries
        # If same country appears more than 4 times, collapse into one record with empty state/city
        country_count = {}
        for item in cleaned_results:
            if isinstance(item, dict) and 'country' in item:
                country = item['country']
                country_count[country] = country_count.get(country, 0) + 1
        
        final_results = []
        countries_to_collapse = {country for country, count in country_count.items() if count >= 4}
        
        for item in cleaned_results:
            if isinstance(item, dict) and 'country' in item:
                country = item['country']
                
                # If this country should be collapsed and we haven't added it yet
                if country in countries_to_collapse:
                    # Check if we already added the collapsed version
                    if not any(r.get('country') == country and r.get('collapsed', False) for r in final_results):
                        # Add collapsed record
                        collapsed_item = {
                            "is_remote": item.get('is_remote', False),
                            "city": "",
                            "state": "",
                            "country": country,
                            "collapsed": True
                        }
                        final_results.append(collapsed_item)
                else:
                    # Keep original record
                    final_results.append(item)

        for item in final_results:
            item.pop('collapsed', None)
        
        for item in final_results:
            if item["country"] in regional_tags:
                single_record = [{
                    "is_remote": item.get('is_remote', False),
                    "city": "",
                    "state": "",
                    "country": "Anywhere in EU"}]
                return single_record

        eu_country_counter = 0

        for item in final_results:
            if item["country"] in eu_countries_list:
                eu_country_counter += 1

        if eu_country_counter >= 4:
            single_record = [{
                    "is_remote": item.get('is_remote', False),
                    "city": "",
                    "state": "",
                    "country": "Anywhere in EU"}]
            return single_record

        
        return final_results
    
    return wrapper
