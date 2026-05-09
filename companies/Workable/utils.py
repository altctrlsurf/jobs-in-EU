
from base.utils import Get, auto_map_countries

class Extract:

    @staticmethod
    @auto_map_countries
    def parse_location_string(job_detail):

        locations = job_detail.get("locations")
        results = []

        is_remote = job_detail.get("remote")
        if not is_remote:
            is_remote = False

        for loc_detail in locations:
            city, state, country = "", "", ""
            country = loc_detail.get("country")
            city = loc_detail.get("city", "")
            hidden = loc_detail.get("hidden")
            if not hidden:
                new_data = {"is_remote": is_remote, "city": city, "state": state, "country": country or ("Europe" if is_remote else None)}
                if new_data not in results:
                    results.append(new_data)

        return results

    @staticmethod
    def extract_description(job_detail):
        description = job_detail.get("description")
        requirements = job_detail.get("requirements")
        benefits = job_detail.get("benefits")

        if requirements:
            requirements = ' <h2 id="job-requirements-title">Requirements</h2> ' + requirements
            description += requirements

        if benefits:
            benefits = ' <h2 id="job-benefits-title">Benefits</h2> ' + benefits
            description += benefits

        return description


    @staticmethod
    def salary_info(job_detail):
        return None, None, None, None
    
    @staticmethod
    def post_date(job_detail):
        post_date = ""
        published_at = job_detail.get("published", "")
        if published_at:
            try:
                post_date = Get.MdyDateStr(published_at)
            except:
                post_date = published_at

        return post_date