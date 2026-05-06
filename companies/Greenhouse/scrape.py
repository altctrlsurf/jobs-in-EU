import os
import csv
from base.config import logger, Output
from base.utils import JobPosting, Get
from .utils import Extract
import json
import time
from typing import Optional
from dataclasses import asdict, dataclass
import dataclasses


SESSION = Get.Session()
BASE_URL   = "https://boards-api.greenhouse.io/v1/boards"
OUTPUT_CSV = "greenhouse_jobs.csv"
REQUEST_DELAY = 0.25
BASE_NAME = "greenhouse"

Out_obj = Output(BASE_NAME)

class Fetch:

    @staticmethod
    def departments(board: str) -> Optional[list]:
        data = Get.Json(f"{BASE_URL}/{board}/departments", SESSION)
        if data is None:
            return None
        return data or []
    
    @staticmethod
    def job_detail(board: str, job_id) -> Optional[dict]:
        return Get.Json(f"{BASE_URL}/{board}/jobs/{job_id}?questions=true", SESSION)


@dataclass
class URLObject:
    name: str = ""
    board: str = ""
    website: str = ""
    logo_link: str = ""


class Read:

    @staticmethod
    def Csv():
        url_csv = os.path.join(os.path.dirname(__file__), 'url.csv')

        with open(url_csv, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            next(reader)
            for row in reader:
                name, url, board, website, logo_link = row
                yield URLObject(name=name, board=board, website=website, logo_link=logo_link)


class Write:

    @staticmethod
    def Jsonl_1():
        url_objs = Read.Csv()
        jsonl_path = Out_obj.get_filename('greenhouse1.jsonl')
        for urlobj in url_objs:
            departments = Fetch.departments(urlobj.board)
            new_json = {"name":urlobj.name, "board":urlobj.board, "website":urlobj.website, "logo_link":urlobj.logo_link, "departments": departments}
            with open(jsonl_path, 'a') as f:
                f.write(json.dumps(new_json))
                f.write('\n')
            time.sleep(REQUEST_DELAY)

    @staticmethod
    def Jsonl_2():
        jsonl1_path = Out_obj.get_filename('greenhouse1.jsonl')

        with open(jsonl1_path, 'r') as f:
            data = [json.loads(line) for line in f if line.strip()]

        for d in data:
            board = d["board"]
            departments = d["departments"]["departments"]

            for department in departments:
                for job in department.get("jobs"):
                    job_id = job.get("id")
                    job_detail = Fetch.job_detail(board, job_id)
                    new_json = {"name": d["name"], 
                                "board": board, 
                                "website": d["website"], 
                                "logo_link": d["logo_link"], 
                                "job_detail_fetch": job_detail}
                    
                    jsonl2_path = Out_obj.get_filename('greenhouse2.jsonl')
                    with open(jsonl2_path, 'a') as f:
                        f.write(json.dumps(new_json))
                        f.write('\n')

                    time.sleep(REQUEST_DELAY)


    def Csv():
        job_postings = []
        jsonl2_path = Out_obj.get_filename('greenhouse2.jsonl')

        with open(jsonl2_path, 'r') as f:
            data = [json.loads(line) for line in f if line.strip()]

        for d in data:
            name, board, website, company_logo, job_detail = d["name"], d["board"], d["website"], d["logo_link"], d["job_detail_fetch"]
            category = job_detail["departments"][0]["name"]
            post_date = job_detail["first_published"]
            post_date = Get.MdyDateStr(post_date)

            description  = Extract.description(job_detail)
            salary_min, salary_max, currency = Extract.salary_info(description)
            if currency is not None:
                salary_period = "annual"
            else:
                salary_period = None 

            job_type = Get.JobType("fulltime")
            expiration_date = ""
            job_title = job_detail["title"]
            job_id = job_detail["id"]

            location_string = job_detail["location"]["name"]

            locations = Extract.location(location_string)
            gh_url = job_detail.get("absolute_url")

            for location in locations:
                is_remote, city, state, country = location["is_remote"], location["city"], location["state"], location["country"]
                if len(locations) == 1:
                    reference_id = Get.ReferenceId("greenhouse", board, job_id)
                else:
                    further_id = f"_{country}_{city}_{state}"
                    further_id = further_id.replace("_None", "").replace(" ", "").replace(',and', '').replace(',', '_')
                    reference_id = Get.ReferenceId("greenhouse", board, job_id, further_id)

                jp_obj = JobPosting()
                jp_obj.reference_id = reference_id
                jp_obj.apply_url = gh_url
                jp_obj.job_url = gh_url
                jp_obj.company_name = name
                jp_obj.company_website = website
                jp_obj.company_logo_url = company_logo
                jp_obj.job_title = job_title
                jp_obj.job_type = job_type
                jp_obj.category = category
                jp_obj.city = city
                jp_obj.state = state
                jp_obj.country = country
                jp_obj.is_remote = str(is_remote).lower()
                jp_obj.salary_from = salary_min
                jp_obj.salary_to = salary_max
                jp_obj.salary_currency = currency
                jp_obj.salary_period = salary_period
                jp_obj.post_date = post_date
                jp_obj.expiration_date = expiration_date
                jp_obj.job_description = description
                job_postings.append(jp_obj)

        output_job_path = Out_obj.get_filename('greenhouse_jobs.csv')
        file_exists = os.path.exists(output_job_path)

        with open(output_job_path, mode='a', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=[field.name for field in dataclasses.fields(JobPosting)])
            
            if not file_exists:
                writer.writeheader()
            
            writer.writerows([asdict(job) for job in job_postings])


def run():
    logger.info("Starting Greenhouse scraper...")
    Write.Jsonl_1()
    Write.Jsonl_2()
    Write.Csv()
