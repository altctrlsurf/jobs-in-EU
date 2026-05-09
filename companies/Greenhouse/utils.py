from bs4 import BeautifulSoup
import re
import html
import pycountry
from base.utils import  auto_map_countries


CUSTOM_REGION_MAP = {
    "US": "United States",
    "USA": "United States",
    "UK": "United Kingdom",
    "UAE": "United Arab Emirates",
    "UK&I": "United Kingdom & Ireland",
    "NORAM": "North America",
    "AMER": "Americas",
    "LATAM": "Latin America",
    "APAC": "Asia-Pacific",
    "EMEA": "Europe, Middle East, and Africa",
    "DACH": "DACH Region",
    "LGC-AMERICAS": "Americas",
    "LCG-AMERICAS": "Americas"
}


CITY_COUNTRY_MAP = {
    "Bangalore": "India",
    "London": "United Kingdom",
    "Dublin": "Ireland",
    "Singapore": "Singapore",
    "Seoul": "South Korea",
    "Austin": "United States",
    "New York": "United States",
    "San Francisco": "United States",
    "San Francisco Bay Area": "United States",
    "Washington": "United States",
    "Washington DC–Baltimore": "United States",
    "Atlanta": "United States",
    "Boston": "United States",
    "Miami": "United States",
    "Raleigh": "United States",
    "Melbourne": "Australia",
    "Sydney": "Australia",
    "Amman": "Jordan",
    "São Paulo": "Brazil",
    "Warsaw": "Poland"
}

def get_country_by_name(name):
    name_clean = name.strip()
    name_upper = name_clean.upper()
    
    if name_upper in CUSTOM_REGION_MAP:
        return CUSTOM_REGION_MAP[name_upper]
        
    try:
        obj = pycountry.countries.lookup(name_clean)
        if hasattr(obj, 'name'):
            return obj.name
    except Exception:
        pass
        
    return None

def get_state_by_name(name):
    try:
        obj = pycountry.subdivisions.lookup(name)
        if hasattr(obj, 'name') and hasattr(obj, 'country_code'):
            return obj
    except Exception:
        pass
        
    return None

def resolve_location(val):
    """Helper to figure out if a string is a city, state, or country."""
    country = get_country_by_name(val)
    if country:
        return None, None, country
        
    matched_city = next((c for c in CITY_COUNTRY_MAP if c.lower() == val.lower()), None)
    if matched_city:
        return matched_city, None, CITY_COUNTRY_MAP[matched_city]
        
    state_obj = get_state_by_name(val)
    if state_obj:
        country_obj = pycountry.countries.get(alpha_2=state_obj.country_code)
        country_name = country_obj.name if country_obj else None
        return None, state_obj.name, country_name
        
    return None, None, val

class Extract:

    @staticmethod
    @auto_map_countries
    def location(loc_str):
        results = []
        parts = loc_str.split(';')
        
        for part in parts:
            part = part.strip()
            if not part:
                continue
            
            is_remote = bool(re.search(r'\bremote\b', part, re.IGNORECASE))
            
            clean_part = re.sub(r'\b(Remote|Hybrid|LGC|LCG)\b', '', part, flags=re.IGNORECASE)
            clean_part = re.sub(r'\s+-\s+', ', ', clean_part)
            clean_part = re.sub(r'\s+–\s+', ', ', clean_part)
            
            tokens = [t.strip(' -–,') for t in clean_part.split(',')]
            tokens = [t for t in tokens if t]
            
            city, state, country = None, None, None
            
            if len(tokens) == 1:
                city, state, country = resolve_location(tokens[0])
                        
            elif len(tokens) == 2:
                val1, val2 = tokens[0], tokens[1]
                _, state2, country2 = resolve_location(val2)
                
                if state2 and country2:
                    city = val1
                    state = state2
                    country = country2
                elif country2 and not state2:
                    _, state1, country1 = resolve_location(val1)
                    if state1:
                        city = None
                        state = state1
                        country = country2
                    else:
                        city = val1
                        state = None
                        country = country2
                else:
                    city = val1
                    state = None
                    country = val2
                        
            elif len(tokens) >= 3:
                city = tokens[0]
                state = tokens[1]
                _, _, country = resolve_location(tokens[-1])
                
            # --- EXPANSION LOGIC ---
            if country == "United Kingdom & Ireland":
                results.append({"is_remote": is_remote, "city": city, "state": state, "country": "United Kingdom"})
                results.append({"is_remote": is_remote, "city": city, "state": state, "country": "Ireland"})
            else:
                results.append({"is_remote": is_remote, "city": city, "state": state, "country": country or ("Europe" if is_remote else None)})
            
        return results


    @staticmethod
    def salary_info(html_content):
        """
        Extract salary information from HTML content.
        
        Args:
            html_content: HTML string or BeautifulSoup object
            
        Returns:
            tuple: (min_salary, max_salary, currency_type) or (None, None, None) if not found
        """

        def sanitize(salary):
            if not salary:
                return None
            return re.sub(r'\D', '', salary)

        if isinstance(html_content, str):
            soup = BeautifulSoup(html_content, 'html.parser')
        else:
            soup = html_content
        
        try:
            pay_range = soup.find('div', class_='pay-range')
            if not pay_range:
                return None, None, None

            pay_text = pay_range.get_text()
            space_split = pay_text.split(" ")
            pay_split = pay_text.split("—")

            currency, min_salary, max_salary = None, None, None

            if space_split:
                currency = space_split[-1]

            if pay_split:
                min_salary = pay_split[0].strip()
                max_salary = pay_split[-1].strip()
                if " " in max_salary:
                    max_salary = max_salary.split(" ")[0]

            return sanitize(min_salary), sanitize(max_salary), currency
                
        except Exception as e:
            print(f"Error extracting salary info: {e}")
            return None, None, None
        
    @staticmethod
    def description(job_detail):
        job_description_full = html.unescape(job_detail["content"])
        return job_description_full
