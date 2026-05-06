import time
import requests
from typing import Optional
from dataclasses import dataclass
from datetime import datetime

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
            return "fulltime"
        if "part" in job_type_str:
            return "parttime"
        if "contract" in job_type_str or "freelance" in job_type_str:
            return "contract"
        return ""
