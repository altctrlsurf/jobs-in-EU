from datetime import datetime

class Extract:

    @staticmethod
    def location(job_detail):

        primary_location = job_detail.get("location")
        results = []

        is_remote = job_detail.get("isRemote")
        if not is_remote:
            is_remote = False

        if primary_location:
            results = [{"is_remote": is_remote, "city": "", "state": "", "country": primary_location}]

        secondary_location = job_detail.get("secondaryLocations")

        for loc_detail in secondary_location:
            city, state, country = "", "", ""

            country = loc_detail.get("location")
            country = country.replace("Remote", "").replace("(", "").replace(")", "")
            address_obj = loc_detail.get("address")
            if address_obj:
                postal_address = address_obj.get("postalAddress")
                if postal_address:
                    city = postal_address.get("addressLocality")
                    state = ""
                    country = postal_address.get("addressCountry")

            results.append({"is_remote": is_remote, "city": city, "state": state, "country": country})

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
            return interval
        
        compensation = job_detail.get("compensation")
        if not compensation:
            return None, None, None, None

        summary_component = compensation.get("summaryComponents")
        if not summary_component:
            return None, None, None, None

        for component in summary_component:
            if component.get("compensationType") == "Salary":
                return component.get("minValue"), component.get("maxValue"), component.get("currencyCode"), interval_map(component.get("interval"))

        return None, None, None, None
    
    @staticmethod
    def description(job_detail):
        description = job_detail.get("descriptionHtml")
        return description

    @staticmethod
    def publish_date(job_detail):
        published_at = job_detail.get("publishedAt", "")
        post_date = ""
        if published_at:
            try:
                dt = datetime.fromisoformat(published_at.replace('+00:00', ''))
                post_date = dt.strftime("%m/%d/%Y")
            except:
                post_date = published_at
        return post_date


