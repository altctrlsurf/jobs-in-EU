
from datetime import datetime
from base.utils import auto_map_countries
class Extract:

    @staticmethod
    @auto_map_countries
    def location(job_detail):
        all_locations = job_detail.get("categories").get("allLocations")
        work_place_type = job_detail.get("workplaceType")
        is_remote = False
        results = []

        if work_place_type == "remote":
            is_remote = True

        if not all_locations:
            return [{"is_remote": is_remote, "city": "", "state": "", "country": ""}]

        for loc_str in all_locations:
            loc_str = loc_str.strip()
            if ',' not in loc_str:
                results.append({"is_remote": is_remote, "city": "", "state": "", "country": loc_str})
            else:
                country, state = loc_str.split(',', 1)
                results.append({"is_remote": is_remote, "city": "", "state": state, "country": country})

        return results


    @staticmethod
    def salary_info(job_detail):

        def interval_map(interval):
            interval_str = interval.lower()
            if "year" in interval_str:
                return "annual"
            elif "month" in interval_str:
                return "monthly"
            elif "hour" in interval_str:
                return "hourly"
            elif "annual" in interval_str:
                return "annual"
            return interval
        
        salary_range = job_detail.get("salaryRange")
        if not salary_range:
            return None, None, None, None
        
        min_val = salary_range.get("min")
        max_val = salary_range.get("max")
        currency = salary_range.get("currency")
        interval = salary_range.get("interval")
        if interval:
            interval = interval_map(interval)
        return min_val, max_val, currency, interval

    @staticmethod
    def description(job_detail):
        description = job_detail.get("description")
        additional = job_detail.get("additional")

        return description + additional
    
    @staticmethod
    def post_date(job_detail):
        created_at = job_detail.get("createdAt", "")
        try:
            dt = datetime.fromtimestamp(int(created_at) / 1000)
            post_date = dt.strftime('%m/%d/%Y')
        except:
            post_date = created_at
        return post_date