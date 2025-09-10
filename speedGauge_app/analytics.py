"""
This module provides the Analytics class, which is used to perform data analysis
on the speedGauge data using SQLAlchemy.
"""
import statistics
import sys
import json
from sqlalchemy import func, case, and_, not_, cast, Date
from flask_app.extensions import db
from flask_app.models.speedgauge import SpeedGaugeData, CompanyAnalytics, DriverAnalytics
from datetime import timedelta

class Analytics:
    """
    A class to perform analytics on speedGauge data using SQLAlchemy.
    """

    def __init__(self):
        """The Analytics class no longer needs a direct db connection utility."""
        pass

    def standard_flow(self):
        self.company_standard_flow()
        self.driver_standard_flow()

    def company_standard_flow(self):
        missing_analytics = self.fetch_missing_company_analytic_dates()
        if not missing_analytics:
            print("Company analytics are already up to date.")
            return

        print(f"Found {len(missing_analytics)} missing company analytic records to process.")
        filter_values = self.determine_data_filter_values()

        for date, generated_records_allowed in missing_analytics:
            analytic_package = self.build_company_analytic_package(
                date, filter_values, generated_records_allowed
            )
            self.insert_company_analytics(
                analytic_package, date, generated_records_allowed, filter_values
            )
        db.session.commit()
        print("Finished committing company analytics.")

    def driver_standard_flow(self):
        missing_driver_analytics = self.fetch_missing_driver_analytic_dates()
        if not missing_driver_analytics:
            print("Driver analytics are already up to date.")
            return

        total_records = len(missing_driver_analytics)
        print(f"Found {total_records} missing driver analytic records to process.")

        # compute filter_values once and reuse
        filter_values = self.determine_data_filter_values()

        # commit batching: change batch_size to taste (1000 original, smaller for dev)
        batch_size = 1000
        for i, (driver_id, date) in enumerate(missing_driver_analytics):
            try:
                # compute and upsert but don't commit each time
                self.insert_driver_analytics(
                    analytic_package={},      # if you build a package, pass it; kept for API parity
                    driver_id=driver_id,
                    start_date=date,
                    filter_values=filter_values,
                    commit=False
                )
            except Exception as exc:
                # log and continue (or you may want to re-raise)
                print(f"[analytics] Error processing driver {driver_id} on {date}: {exc}")
                db.session.rollback()
                continue

            # batch commit periodically to avoid huge transactions
            if (i + 1) % batch_size == 0:
                try:
                    db.session.commit()
                    print(f"Committed {i + 1}/{total_records} driver records...")
                except Exception as exc:
                    db.session.rollback()
                    print(f"[analytics] Commit failed after {i + 1} records: {exc}", file=sys.stderr)
                    raise

        # final commit for remaining records
        try:
            db.session.commit()
            print(f"Finished committing all {total_records} driver records.")
        except Exception:
            db.session.rollback()
            print("[analytics] Final commit failed for driver analytics", file=sys.stderr)
            raise

    def fetch_full_date_list(self):
        results = db.session.query(SpeedGaugeData.start_date).distinct().order_by(SpeedGaugeData.start_date).all()
        return [row.start_date for row in results]

    def fetch_missing_company_analytic_dates(self):
        full_date_list = self.fetch_full_date_list()
        
        existing_analytics_q = db.session.query(CompanyAnalytics.start_date, CompanyAnalytics.generated_records_allowed).all()
        existing_analytics = set(existing_analytics_q)

        required_analytics = set()
        for date in full_date_list:
            required_analytics.add((date, True))
            required_analytics.add((date, False))

        return list(required_analytics - existing_analytics)

    def determine_data_filter_values(self, stdev_threshold=1):
        columns = ["percent_speeding", "distance_driven"]
        data_set = {}

        for column_name in columns:
            column = getattr(SpeedGaugeData, column_name)
            result = db.session.query(
                func.avg(column).label('avg'),
                func.stddev(column).label('stddev')
            ).filter(SpeedGaugeData.is_interpolated == 0).one()

            avg = float(result.avg) if result.avg else 0
            stddev = float(result.stddev) if result.stddev else 0

            max_val = avg + (stdev_threshold * stddev)
            min_val = avg - (stdev_threshold * stddev)

            data_set[f'{column_name}_max'] = round(max_val, 2)
            data_set[f'{column_name}_min'] = 0 if column_name == "percent_speeding" else round(min_val, 2)
        
        data_set['stdev_threshold'] = stdev_threshold
        return data_set

    def build_company_analytic_package(
        self,
        date,
        filter_data,
        generated_records_allowed=False
    ):
        # This method can be simplified or expanded based on exact analytics needs.
        # For now, it mimics the structure of the old one.
        return {}
    
    def insert_company_analytics(self, analytic_package, start_date, generated_records_allowed, filter_values, commit=True):
        """
        Compute company-level analytics for `start_date` and either insert or update
        a CompanyAnalytics row. This computes all stats first, then upserts the DB row,
        so we avoid autoflush inserting a partially-populated record.
        """

        # 1) Compute the total row count (honoring generated_records_allowed)
        count_q = db.session.query(func.count(SpeedGaugeData.id)).filter(
            SpeedGaugeData.start_date == start_date
        )
        if not generated_records_allowed:
            count_q = count_q.filter(SpeedGaugeData.is_interpolated == 0)
        total_count = count_q.scalar() or 0
        print(f"[analytics] total_count for {start_date} (generated_allowed={generated_records_allowed}) = {total_count}")

        # 2) For each column compute stats into a local dict
        columns = ["percent_speeding", "distance_driven"]
        computed = {
            "records_count": total_count,
            "std_filter_value": filter_values.get("stdev_threshold"),
            # per-column values will go under keys like avg_percent_speeding, median_distance_driven, etc.
        }

        for col_name in columns:
            column = getattr(SpeedGaugeData, col_name)
            filter_min = filter_values.get(f"{col_name}_min")
            filter_max = filter_values.get(f"{col_name}_max")

            print(f"[analytics] computing stats for {col_name}: min={filter_min}, max={filter_max}")

            # Aggregate stats: count, avg, max, min, stddev
            agg_q = db.session.query(
                func.count(column).label("count"),
                func.avg(column).label("avg"),
                func.max(column).label("max"),
                func.min(column).label("min"),
                func.stddev(column).label("stddev")
            ).filter(
                SpeedGaugeData.start_date == start_date,
                column >= filter_min,
                column <= filter_max
            )
            if not generated_records_allowed:
                agg_q = agg_q.filter(SpeedGaugeData.is_interpolated == 0)

            # .one() returns a row-like object with named attributes
            stats = agg_q.one()
            # Make Python-friendly values (None -> keep None, numeric strings -> float)
            count_val = int(stats.count or 0)
            avg_val = float(stats.avg) if stats.avg is not None else None
            max_val = float(stats.max) if stats.max is not None else None
            min_val = float(stats.min) if stats.min is not None else None
            std_val = float(stats.stddev) if stats.stddev is not None else None

            # Median: gather values (ok for modest row counts)
            median_q = db.session.query(column).filter(
                SpeedGaugeData.start_date == start_date,
                column >= filter_min,
                column <= filter_max
            )
            if not generated_records_allowed:
                median_q = median_q.filter(SpeedGaugeData.is_interpolated == 0)
            values = [r[0] for r in median_q.all()]
            median_val = statistics.median(values) if values else None

            # store computed values into the dict with consistent keys
            computed[f"count_{col_name}"] = count_val
            computed[f"avg_{col_name}"] = avg_val
            computed[f"max_{col_name}"] = max_val
            computed[f"min_{col_name}"] = min_val
            computed[f"std_{col_name}"] = std_val
            computed[f"median_{col_name}"] = median_val

            print(f"[analytics] {col_name} -> count={count_val}, avg={avg_val}, median={median_val}")

        # --- Generate Trend JSON ---
        trend_end_date = start_date
        trend_start_date = trend_end_date - timedelta(days=365)

        trend_data_q = db.session.query(
            cast(SpeedGaugeData.start_date, Date).label('date'),
            func.avg(SpeedGaugeData.percent_speeding).label('avg_speeding'),
            func.sum(SpeedGaugeData.distance_driven).label('total_distance')
        ).filter(
            SpeedGaugeData.start_date.between(trend_start_date, trend_end_date)
        ).group_by(
            cast(SpeedGaugeData.start_date, Date)
        ).order_by(
            cast(SpeedGaugeData.start_date, Date).asc()
        ).all()

        speeding_trend = {}
        distance_trend = {}
        for row in trend_data_q:
            speeding_trend[row.date.isoformat()] = float(row.avg_speeding) if row.avg_speeding is not None else 0
            distance_trend[row.date.isoformat()] = float(row.total_distance) if row.total_distance is not None else 0

        computed['speeding_trend_json'] = json.dumps(speeding_trend)
        computed['distance_trend_json'] = json.dumps(distance_trend)

        # 3) Upsert the CompanyAnalytics row now that we have all values
        record = db.session.query(CompanyAnalytics).filter_by(
            start_date=start_date,
            generated_records_allowed=generated_records_allowed
        ).one_or_none()

        if not record:
            record = CompanyAnalytics(
                start_date=start_date,
                generated_records_allowed=generated_records_allowed
            )
            db.session.add(record)

        # assign the computed fields to the record
        record.records_count = computed.get("records_count", 0)
        record.std_filter_value = computed.get("std_filter_value")

        for col_name in columns:
            setattr(record, f"avg_{col_name}", computed.get(f"avg_{col_name}"))
            setattr(record, f"max_{col_name}", computed.get(f"max_{col_name}"))
            setattr(record, f"min_{col_name}", computed.get(f"min_{col_name}"))
            setattr(record, f"std_{col_name}", computed.get(f"std_{col_name}"))
            setattr(record, f"median_{col_name}", computed.get(f"median_{col_name}"))

        record.speeding_trend_json = computed.get("speeding_trend_json")
        record.distance_trend_json = computed.get("distance_trend_json")

        # Optionally commit here or let caller commit (company_standard_flow currently commits after loop)
        if commit:
            try:
                db.session.commit()
                print(f"[analytics] committed CompanyAnalytics for {start_date} (generated={generated_records_allowed})")
            except Exception:
                db.session.rollback()
                print("[analytics] commit failed", file=sys.stderr)
                raise

        return record
    
    def fetch_missing_driver_analytic_dates(self):
        subquery = db.session.query(DriverAnalytics.driver_id, DriverAnalytics.start_date).subquery()
        
        missing = db.session.query(SpeedGaugeData.driver_id, SpeedGaugeData.start_date).distinct().outerjoin(subquery, and_(
                SpeedGaugeData.driver_id == subquery.c.driver_id,
                SpeedGaugeData.start_date == subquery.c.start_date
            )).filter(subquery.c.driver_id == None).all()
            
        return missing

    def build_driver_analytic_package(self, driver_id, date, filter_values):
        # This method is also simplified. The logic is moved to insert_driver_analytics
        return {}

    def insert_driver_analytics(self, analytic_package, driver_id, start_date, filter_values=None, commit=True):
        if filter_values is None:
            filter_values = self.determine_data_filter_values()

        # 1-year window for main stats
        start_date_minus = start_date - timedelta(days=365)

        # total rows in 1-year window
        count_q = db.session.query(func.count(SpeedGaugeData.id)).filter(
            SpeedGaugeData.driver_id == driver_id,
            SpeedGaugeData.start_date.between(start_date_minus, start_date)
        )
        total_count = count_q.scalar() or 0

        computed = {
            "records_count": total_count,
            # placeholders for week metrics - we'll fill them
            "current_week_percent_speeding": 0,
            "previous_week_percent_speeding": 0,
            "current_week_distance_driven": 0,
            "previous_week_distance_driven": 0,
        }

        # --- compute current & previous week ranges (7-day windows) ---
        current_week_start = start_date - timedelta(days=6)  # inclusive 7 days: start_date-6 .. start_date
        prev_week_end = current_week_start - timedelta(days=1)
        prev_week_start = prev_week_end - timedelta(days=6)

        # helper to compute avg for a column in a date range (returns None or numeric)
        def avg_in_range(column, date_from, date_to, driver_only=True):
            q = db.session.query(func.avg(column)).filter(
                column is not None  # no-op placeholder - we'll add proper filters next
            )
            # build filters
            if driver_only:
                q = db.session.query(func.avg(column)).filter(
                    SpeedGaugeData.driver_id == driver_id,
                    SpeedGaugeData.start_date.between(date_from, date_to)
                )
            else:
                q = db.session.query(func.avg(column)).filter(
                    SpeedGaugeData.start_date.between(date_from, date_to)
                )
            # You may also want to apply min/max filters here (filter_values)
            # For simplicity, we won't apply the stdev filters to weekly averages here.
            val = q.scalar()
            return float(val) if val is not None else None

        # compute weekly averages (or totals for distance if desired)
        # percent_speeding -> avg percentage
        cur_pct = avg_in_range(getattr(SpeedGaugeData, "percent_speeding"), current_week_start, start_date)
        prev_pct = avg_in_range(getattr(SpeedGaugeData, "percent_speeding"), prev_week_start, prev_week_end)
        computed["current_week_percent_speeding"] = cur_pct if cur_pct is not None else 0
        computed["previous_week_percent_speeding"] = prev_pct if prev_pct is not None else 0

        # distance_driven -> sum or avg? here I use avg; change to SUM if you prefer totals
        def sum_in_range(column, date_from, date_to):
            q = db.session.query(func.sum(column)).filter(
                SpeedGaugeData.driver_id == driver_id,
                SpeedGaugeData.start_date.between(date_from, date_to)
            )
            val = q.scalar()
            return float(val) if val is not None else None

        cur_dist = sum_in_range(getattr(SpeedGaugeData, "distance_driven"), current_week_start, start_date)
        prev_dist = sum_in_range(getattr(SpeedGaugeData, "distance_driven"), prev_week_start, prev_week_end)
        computed["current_week_distance_driven"] = cur_dist if cur_dist is not None else 0
        computed["previous_week_distance_driven"] = prev_dist if prev_dist is not None else 0

        # percent change and abs change (guard divide-by-zero)
        def pct_change(current, previous):
            if previous in (None, 0):
                return 0 if current is not None else 0
            return (current - previous) / previous

        computed["percent_change_percent_speeding"] = pct_change(computed["current_week_percent_speeding"],
                                                                computed["previous_week_percent_speeding"])
        computed["abs_change_percent_speeding"] = abs(computed["current_week_percent_speeding"] - computed["previous_week_percent_speeding"])
        computed["percent_change_distance_driven"] = pct_change(computed["current_week_distance_driven"],
                                                                computed["previous_week_distance_driven"])
        computed["abs_change_distance_driven"] = abs(computed["current_week_distance_driven"] - computed["previous_week_distance_driven"])

        # --- compute the long-term aggregates per column (1-year window, filtered by min/max) ---
        columns = ["percent_speeding", "distance_driven"]
        for col_name in columns:
            column = getattr(SpeedGaugeData, col_name)
            filter_min = filter_values.get(f"{col_name}_min")
            filter_max = filter_values.get(f"{col_name}_max")

            agg_q = db.session.query(
                func.count(column).label("count"),
                func.avg(column).label("avg"),
                func.max(column).label("max"),
                func.min(column).label("min"),
                func.stddev(column).label("stddev")
            ).filter(
                SpeedGaugeData.driver_id == driver_id,
                SpeedGaugeData.start_date.between(start_date_minus, start_date),
                column >= filter_min,
                column <= filter_max
            )

            stats = agg_q.one()
            computed[f"avg_{col_name}"] = float(stats.avg) if stats.avg is not None else None
            computed[f"max_{col_name}"] = float(stats.max) if stats.max is not None else None
            computed[f"min_{col_name}"] = float(stats.min) if stats.min is not None else None
            computed[f"std_{col_name}"] = float(stats.stddev) if stats.stddev is not None else None

            # median
            median_q = db.session.query(column).filter(
                SpeedGaugeData.driver_id == driver_id,
                SpeedGaugeData.start_date.between(start_date_minus, start_date),
                column >= filter_min,
                column <= filter_max
            ).order_by(column)
            vals = [r[0] for r in median_q.all()]
            computed[f"median_{col_name}"] = statistics.median(vals) if vals else None

            # count per column might be useful, but db schema likely has a single records_count
            computed[f"count_{col_name}"] = int(stats.count or 0)

        # --- Generate Trend JSON ---
        trend_end_date = start_date
        trend_start_date = trend_end_date - timedelta(days=365)

        trend_data_q = db.session.query(
            SpeedGaugeData.start_date,
            SpeedGaugeData.percent_speeding,
            SpeedGaugeData.distance_driven
        ).filter(
            SpeedGaugeData.driver_id == driver_id,
            SpeedGaugeData.start_date.between(trend_start_date, trend_end_date)
        ).order_by(SpeedGaugeData.start_date.asc()).all()

        speeding_trend = {}
        distance_trend = {}
        for row in trend_data_q:
            speeding_trend[row.start_date.isoformat()] = float(row.percent_speeding) if row.percent_speeding is not None else 0
            distance_trend[row.start_date.isoformat()] = float(row.distance_driven) if row.distance_driven is not None else 0

        computed['speeding_trend_json'] = json.dumps(speeding_trend)
        computed['distance_trend_json'] = json.dumps(distance_trend)

        # --- Upsert the DriverAnalytics row using computed dict ---
        try:
            record = db.session.query(DriverAnalytics).filter_by(driver_id=driver_id, start_date=start_date).one_or_none()
            if not record:
                record = DriverAnalytics(driver_id=driver_id, start_date=start_date)
                db.session.add(record)

            # map computed to record; use defaults where DB requires NOT NULL
            record.std_filter_threshold = filter_values.get("stdev_threshold")
            record.current_week_percent_speeding = computed.get("current_week_percent_speeding", 0)
            record.previous_week_percent_speeding = computed.get("previous_week_percent_speeding", 0)
            record.percent_change_percent_speeding = computed.get("percent_change_percent_speeding", 0)
            record.abs_change_percent_speeding = computed.get("abs_change_percent_speeding", 0)

            record.max_percent_speeding = computed.get("max_percent_speeding", computed.get("max_percent_speeding") or computed.get("max_percent_speeding"))
            record.min_percent_speeding = computed.get("min_percent_speeding", computed.get("min_percent_speeding") or computed.get("min_percent_speeding"))
            record.avg_percent_speeding = computed.get("avg_percent_speeding")
            record.median_percent_speeding = computed.get("median_percent_speeding")
            record.std_percent_speeding = computed.get("std_percent_speeding")

            record.current_week_distance_driven = computed.get("current_week_distance_driven", 0)
            record.previous_week_distance_driven = computed.get("previous_week_distance_driven", 0)
            record.percent_change_distance_driven = computed.get("percent_change_distance_driven", 0)
            record.abs_change_distance_driven = computed.get("abs_change_distance_driven", 0)

            record.max_distance_driven = computed.get("max_distance_driven")
            record.min_distance_driven = computed.get("min_distance_driven")
            record.avg_distance_driven = computed.get("avg_distance_driven")
            record.median_distance_driven = computed.get("median_distance_driven")
            record.std_distance_driven = computed.get("std_distance_driven")

            record.speeding_trend_json = computed.get("speeding_trend_json")
            record.distance_trend_json = computed.get("distance_trend_json")

            record.records_count = computed.get("records_count", 0)

            # optionally commit here or let caller batch commit
            if commit:
                db.session.commit()
            return record

        except Exception as exc:
            # helpful debug before re-raising or returning
            print("[analytics] Failed to upsert DriverAnalytics for", driver_id, start_date, "computed:", computed, file=sys.stderr)
            db.session.rollback()
            raise
