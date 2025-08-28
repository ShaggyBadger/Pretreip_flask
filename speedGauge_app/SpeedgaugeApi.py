from datetime import datetime, timedelta
from flask_app.extensions import db
from flask_app.models import SpeedGaugeData, DriverAnalytics, CompanyAnalytics


class Api:
    """
    this is the main way to get the data for a user. should return dicts and stuff
    """

    def __init__(self, driver_id):
        self.driver_id = driver_id

    def build_speedgauge_report(self):
        """
        returns a list of dicts of speedgauge rows for that date
        """
        rows = SpeedGaugeData.query.filter_by(driver_id=self.driver_id).order_by(SpeedGaugeData.start_date.desc()).all()

        # Clean the row dicts if needed, make url short etc etc
        cleaned_row_dicts = [self.clean_dict(row.__dict__) for row in rows]

        return cleaned_row_dicts

    def clean_dict(self, row_dict):
        keys_to_remove = ["raw_json", "is_interpolated", "id", "_sa_instance_state"]

        for i in keys_to_remove:
            if i in row_dict:
                del row_dict[i]

        if "url" in row_dict and row_dict["url"] and len(row_dict["url"]) > 10:
            url = row_dict["url"]
            row_dict["url"] = (
                f'<a href="{url}" target="_blank" rel="noopener noreferrer">Click for map</a>'
            )

        return row_dict

    def get_speedGauge_row(self, start_date):
        """
        this takes in the start_date and returns the row of data in dict form from the db
        """
        row = SpeedGaugeData.query.filter_by(driver_id=self.driver_id, start_date=start_date).first()
        if row:
            return row.__dict__
        return None


    def get_dates(self, cuttoff_time=365):
        """
        default cuttoff time is a year, although you can override if you want. just do it with num days

        Returns a list full of start_date in ASC order. oldest date is first, newest date is index[-1]

        the date is str from db, it can be used for query and also turned into datetime object later
        """
        cuttoff_date = datetime.now() - timedelta(days=cuttoff_time)

        dates = db.session.query(SpeedGaugeData.start_date).order_by(SpeedGaugeData.start_date.asc()).all()

        filtered_list = []

        for date in dates:
            start_date = date[0]

            if start_date is not None and start_date >= cuttoff_date:
                filtered_list.append(start_date.isoformat())

        return filtered_list

    def extract_data(self, info):
        """
        takes in a dictionary of data from a row in the db and creates a new dict of info for the template to use in making the webpage
        """
        extracted_data = {
            "fname": info["first_name"],
            "lname": info["last_name"],
            "driver_id": info["driver_id"],
        }

        return extracted_data

    def get_driver_analytics(self, driver_id, start_date):
        """
        Returns the driver analytic package for a given driver_id and start_date.
        """
        analytic_data = DriverAnalytics.query.filter_by(driver_id=driver_id, start_date=start_date).first()
        
        return analytic_data

    def get_company_analytics(self, start_date, generated_records_allowed=True):
        """
        Returns the company analytic package for a given start_date and generated_records_allowed status.
        """
        analytic_data = CompanyAnalytics.query.filter_by(start_date=start_date, generated_records_allowed=generated_records_allowed).first()

        return analytic_data
