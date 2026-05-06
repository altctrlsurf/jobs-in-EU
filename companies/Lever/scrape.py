
from .utils import Extract
import os
import csv
from base.config import logger, Output
from base.utils import JobPosting, Get
import json
import time
from typing import Optional
from dataclasses import asdict, dataclass
import dataclasses


SESSION = Get.Session()
OUTPUT_CSV = "lever_jobs.csv"
REQUEST_DELAY = 0.25
BASE_NAME = "lever"

Out_obj = Output(BASE_NAME)

class Fetch:

    @staticmethod
    def job_list(board: str) -> Optional[dict]:
        lever_api = f'https://api.lever.co/v0/postings/{board}'
        return Get.Json(lever_api, SESSION)
    
    @staticmethod
    def job_detail(board: str, job_id: str) -> Optional[dict]:
        lever_api = f'https://api.lever.co/v0/postings/{board}/{job_id}'
        return Get.Json(lever_api, SESSION)


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
        jsonl_path = Out_obj.get_filename('lever1.jsonl')
        for urlobj in url_objs:
            job_detail = Fetch.job_list(urlobj.board)
            new_json = {"name":urlobj.name, "board":urlobj.board, "website":urlobj.website, "logo_link":urlobj.logo_link, "job_detail_fetch": job_detail}
            with open(jsonl_path, 'a') as f:
                f.write(json.dumps(new_json))
                f.write('\n')
            time.sleep(REQUEST_DELAY)


    def Csv():
        job_postings = []
        jsonl1_path = Out_obj.get_filename('lever1.jsonl')

        with open(jsonl1_path, 'r') as f:
            data = [json.loads(line) for line in f if line.strip()]

        for d in data:
            name, board, website, company_logo, job_data_all = d["name"], d["board"], d["website"], d["logo_link"], d["job_detail_fetch"]

            for job_data in job_data_all:
                job_id = job_data.get("id", "")
                salary_from, salary_to, salary_currency, salary_period = Extract.salary_info(job_data)
                post_date = Extract.post_date(job_data)
                locations = Extract.location(job_data)
                description = Extract.description(job_data)
                
                for location in locations:
                    is_remote, city, state, country = location["is_remote"], location["city"], location["state"], location["country"]
                    if len(locations) == 1:
                        reference_id = Get.ReferenceId("lever", board, job_id)
                    else:
                        further_id = f"_{country}_{city}_{state}"
                        further_id = further_id.replace("_None", "").replace(" ", "").replace(',and', '').replace(',', '_')
                        reference_id = Get.ReferenceId("lever", board, job_id, further_id)
                    
                    job_url = job_data.get("hostedUrl", "")
                    apply_url = job_data.get("applyUrl", "")


                    jp_obj = JobPosting()
                    jp_obj.reference_id = reference_id
                    jp_obj.apply_url = apply_url
                    jp_obj.job_url = job_url
                    jp_obj.company_name = name
                    jp_obj.company_website = website
                    jp_obj.company_logo_url = company_logo
                    jp_obj.job_title = job_data.get("text", "")
                    jp_obj.job_type = Get.JobType(job_data.get("categories", "").get("commitment", ""))
                    jp_obj.category = job_data.get("categories", "").get("team", "")
                    jp_obj.city = city
                    jp_obj.state = state
                    jp_obj.country = country
                    jp_obj.is_remote = 'true' if str(is_remote).lower().startswith('t') else 'false'
                    jp_obj.salary_from = salary_from
                    jp_obj.salary_to = salary_to
                    jp_obj.salary_currency = salary_currency
                    jp_obj.salary_period = salary_period
                    jp_obj.post_date = post_date
                    jp_obj.expiration_date = ""
                    jp_obj.job_description = description

                    job_postings.append(jp_obj)
        
        output_job_path = Out_obj.get_filename('lever_jobs.csv')
        file_exists = os.path.exists(output_job_path)

        with open(output_job_path, mode='a', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=[field.name for field in dataclasses.fields(JobPosting)])
            
            if not file_exists:
                writer.writeheader()
            
            writer.writerows([asdict(job) for job in job_postings])

def run():
    logger.info("Starting Lever scraper...")
    Write.Jsonl_1()
    Write.Csv()
