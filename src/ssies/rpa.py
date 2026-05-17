from .ssies import SSIES
from ssies.schemes import HEADER_SCHEMA_2, RPA_SCHEMA
import xarray as xr
import numpy as np
import pandas as pd


class RPA(SSIES):

    def _is_valid_header(self, header):
        spacecraft_id = header["spacecraft_id"]
        data_file_id = header["data_file_id"]
        number_set = header["number_set"]

        if data_file_id not in {"RPADWS", "RPADWF"}:
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

        if not (1 <= number_set <= 15):
            return False

        return True

    def parse_file(self):
        records = []

        with self._open_file() as file:
            while True:
                try:
                    minute_record = self._parse_minute_record(
                        file,
                        HEADER_SCHEMA_2,
                        RPA_SCHEMA,
                        "number_set"
                    )
                    records.append(minute_record)

                except EOFError:
                    break

                except (ValueError, UnicodeDecodeError):
                    if not self._resync_to_next_header(file, HEADER_SCHEMA_2):
                        break

        ds = self._to_xarray(records)

        return ds

    def _to_xarray(self, records):
        if not records:
            return xr.Dataset()

        attr_fields = {
            "spacecraft_id",
            "data_file_id",
        }

        minute_schema = [
            f for f in HEADER_SCHEMA_2
            if f["name"] not in attr_fields
        ]

        minute_names = [f["name"] for f in minute_schema]
        set_names = [f["name"] for f in RPA_SCHEMA]

        minute_times = []
        minute_index_per_set = []
        set_times = []

        minute_values = {n: [] for n in minute_names}
        set_values = {n: [] for n in set_names}

        for m_idx, minute_record in enumerate(records):
            header = minute_record["header"]

            minute_time = self._build_minute_time(header)
            minute_times.append(minute_time)

            for n in minute_names:
                minute_values[n].append(header[n])

            for set_record in minute_record["data"]:
                minute_index_per_set.append(m_idx)

                set_times.append(
                    self._build_time(
                        header,
                        set_record["second_of_minute"],
                    )
                )

                for n in set_names:
                    set_values[n].append(set_record[n])

        ds = xr.Dataset(
            coords={
                "minute": ("minute",np.arange(len(records), dtype=np.int64)),
                "minute_time": ("minute",minute_times),
                "set": ("set",set_times),
                "minute_index": ("set",minute_index_per_set),
            }
        )

        for n in minute_names:
            ds[n] = ("minute",minute_values[n])

        for n in set_names:
            ds[n] = ("set",set_values[n])

        first_header = records[0]["header"]

        ds.attrs["source_file"] = str(self.filepath)
        ds.attrs["spacecraft_id"] = first_header.get("spacecraft_id")
        ds.attrs["data_file_id"] = first_header.get("data_file_id")
        ds.attrs["minute_count"] = len(records)
        ds.attrs["record_count"] = len(set_times)

        self._apply_schema_attrs(ds, minute_schema)
        self._apply_schema_attrs(ds, RPA_SCHEMA)

        ds["minute_time"].attrs["long_name"] = "Date and time for the minute"
        ds["set"].attrs["long_name"] = "Coordinate for sets"
        ds["minute_index"].attrs["long_name"] = "Link between minute and set"
        ds["minute"].attrs["long_name"] = "Coordinate for sets minute"

        return ds

    def _to_flat_dataframe(self, ds):
        set_vars = [
            name for name in ds.data_vars
            if "set" in ds[name].dims
        ]

        set_df = pd.DataFrame({
            name: ds[name].values
            for name in set_vars
        })

        set_df["minute_index"] = ds["minute_index"].values

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
            set_df,
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