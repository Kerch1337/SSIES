from .ssies import SSIES
from ssies.schemes import HEADER_SCHEMA, SM_SCHEMA
import xarray as xr
import numpy as np
import pandas as pd


class SM(SSIES):

    def _is_valid_header(self, header):
        spacecraft_id = header["spacecraft_id"]
        data_file_id = header["data_file_id"]
        seconds_in_minute = header["seconds_in_minute"]

        if data_file_id != "SM":
            return False

        if not spacecraft_id.startswith("F"):
            return False

        try:
            flight_number = int(spacecraft_id[1:])
        except ValueError:
            return False

        if not (8 <= flight_number <= 15):
            return False

        if not (1987 <= header["year"] <= 2049):
            return False

        if not (0 <= header["day_of_year"] <= 366):
            return False

        if not (0 <= header["hour"] <= 24):
            return False

        if not (0 <= header["minute_of_hour"] <= 59):
            return False

        if not (1 <= seconds_in_minute <= 60):
            return False

        return True

    def parse_file(self):
        records = []

        with self._open_file() as file:
            while True:
                try:
                    minute_record = self._parse_minute_record(file, HEADER_SCHEMA, SM_SCHEMA,"seconds_in_minute")
                    records.append(minute_record)

                except EOFError:
                    break

                except (ValueError, UnicodeDecodeError):
                    if not self._resync_to_next_header(file, HEADER_SCHEMA):
                        break

        ds = self._to_xarray(records)

        return ds

    def _to_xarray(self, records):
        if not records:
            return xr.Dataset()

        attr_fields = {"spacecraft_id", "data_file_id"}

        minute_schema = [
            f for f in HEADER_SCHEMA
            if f["name"] not in attr_fields
        ]

        minute_names = [f["name"] for f in minute_schema]
        second_names = [f["name"] for f in SM_SCHEMA]

        minute_times = []
        minute_index_per_second = []
        second_times = []

        minute_values = {n: [] for n in minute_names}
        second_values = {n: [] for n in second_names}

        for m_idx, minute_record in enumerate(records):
            header = minute_record["header"]

            minute_time = self._build_minute_time(header)
            minute_times.append(minute_time)

            for n in minute_names:
                minute_values[n].append(header[n])

            for second_record in minute_record["data"]:
                minute_index_per_second.append(m_idx)

                second_times.append(
                    self._build_time(
                        header,
                        second_record["second_of_minute"],
                    )
                )

                for n in second_names:
                    second_values[n].append(second_record[n])

        ds = xr.Dataset(
            coords={
                "minute": ("minute", np.arange(len(records), dtype=np.int64)),
                "minute_time": ("minute", minute_times),
                "second": ("second", second_times),
                "minute_index": ("second", minute_index_per_second),
            }
        )

        for n in minute_names:
            ds[n] = ("minute", minute_values[n])

        for n in second_names:
            ds[n] = ("second", second_values[n])

        first_header = records[0]["header"]

        ds.attrs["source_file"] = str(self.filepath)
        ds.attrs["spacecraft_id"] = first_header.get("spacecraft_id")
        ds.attrs["data_file_id"] = first_header.get("data_file_id")
        ds.attrs["minute_count"] = len(records)
        ds.attrs["record_count"] = len(second_times)

        self._apply_schema_attrs(ds, minute_schema)
        self._apply_schema_attrs(ds, SM_SCHEMA)

        ds["minute_time"].attrs["long_name"] = "Date and time for the minute"
        ds["second"].attrs["long_name"] = "Coordinate for seconds"
        ds["minute_index"].attrs["long_name"] = "Link between minute and second"
        ds["minute"].attrs["long_name"] = "Coordinate for minutes"

        return ds

    def _to_flat_dataframe(self, ds):
        second_vars = [
            name for name in ds.data_vars
            if "second" in ds[name].dims
        ]

        second_df = pd.DataFrame({
            name: ds[name].values
            for name in second_vars
        })

        second_df["minute_index"] = ds["minute_index"].values

        minute_vars = [
            name for name in ds.data_vars
            if "minute" in ds[name].dims
        ]

        minute_df = pd.DataFrame({
            name: ds[name].values
            for name in minute_vars
        })

        minute_df["minute_index"] = np.arange(
            ds.sizes["minute"],
            dtype=np.int64
        )

        flat = minute_df.merge(
            second_df,
            on="minute_index",
            how="left",
        )

        flat = flat.drop(columns=["minute_index"])

        spacecraft_id = ds.attrs.get("spacecraft_id")
        data_file_id = ds.attrs.get("data_file_id")

        flat.insert(0, "data_file_id", data_file_id)
        flat.insert(0, "spacecraft_id", spacecraft_id)

        return flat

    def export_csv(self, ds, path):
        flat = self._to_flat_dataframe(ds)
        flat.to_csv(path, index=False)