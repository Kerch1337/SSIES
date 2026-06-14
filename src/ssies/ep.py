from .ssies import SSIES
from ssies.schemes import HEADER_SCHEMA_2, EP_OUTPUT_TYPE_SCHEMA, EP_BS_SCHEMA, EP_D_SCHEMA
import xarray as xr
import numpy as np
import pandas as pd
from pathlib import Path
import gzip


class EP(SSIES):

    def _is_valid_header(self, header: dict) -> bool:
        spacecraft_id = header["spacecraft_id"]
        data_file_id = header["data_file_id"]
        number_set = header["number_set"]

        if data_file_id != "ELEC":
            return False

        if not spacecraft_id.startswith("F"):
            return False

        try:
            flight_number = int(spacecraft_id[1:])
        except ValueError:
            return False

        if not (8 <= flight_number <= 15):
            return False

        if not (0 <= header["day_of_year"] <= 366):
            return False

        if not (0 <= header["hour"] <= 24):
            return False

        if not (0 <= header["minute_of_hour"] <= 59):
            return False

        if not (1 <= number_set <= 30):
            return False

        return True

    def _parse_output_types(self, file: gzip.GzipFile) -> list:
        output_types = []

        for i in range(30):
            record = self._parse_schema(file,EP_OUTPUT_TYPE_SCHEMA)

            output_type = record["output_type"].replace("\x00", "").strip()

            output_types.append(output_type)

        return output_types

    def _parse_set_record(self, file: gzip.GzipFile, output_type: str) -> dict | None:

        start = file.tell()

        file.seek(start)

        if output_type in {"B", "S", "O"}:
            record = self._parse_schema(file, EP_BS_SCHEMA)
            record["output_type"] = output_type
            return record

        if output_type == "D":
            record = self._parse_schema(file, EP_D_SCHEMA)
            record["output_type"] = output_type
            return record

    def _parse_minute_record(self, file: gzip.GzipFile, header_scheme: list[dict], set_scheme: list[dict], field_name: str) -> dict:
        start_offset = file.tell()

        header = self._parse_schema(file, header_scheme)

        if not self._is_valid_header(header):
            raise ValueError(f"Invalid EP header at offset {start_offset}: {header}")

        output_types = self._parse_output_types(file)
        output_types = output_types[:header[field_name]]

        data = []

        for output_type in output_types:

            if output_type not in {"B", "S", "D", "O"}:
                continue

            set_record = self._parse_set_record(file,output_type)

            data.append(set_record)

        return {
            "header": header,
            "data": data,
        }

    def parse_file(self) -> xr.Dataset:

        records = []

        with self._open_file() as file:
            while True:
                try:
                    minute_record = self._parse_minute_record(file, HEADER_SCHEMA_2, None, "number_set")
                    records.append(minute_record)

                except EOFError:
                    break

                except (ValueError, UnicodeDecodeError):
                    if not self._resync_to_next_header(file, HEADER_SCHEMA_2):
                        break

        ds = self._to_xarray(records)

        return ds

    def _to_xarray(self, records: list[dict]) -> xr.Dataset:
        if not records:
            return xr.Dataset()

        attr_fields = {"spacecraft_id", "data_file_id"}

        minute_schema = [f for f in HEADER_SCHEMA_2 if f["name"] not in attr_fields]
        minute_names = [f["name"] for f in minute_schema]
        bs_names = [f["name"] for f in EP_BS_SCHEMA]
        d_names = [f["name"] for f in EP_D_SCHEMA]

        minute_times = []
        minute_index_per_bs = []
        minute_index_per_d = []
        bs_times = []
        d_times = []

        minute_values = {n: [] for n in minute_names}
        bs_values = {n: [] for n in bs_names}
        d_values = {n: [] for n in d_names}
        bs_output_types = []
        d_output_types = []

        for m_idx, minute_record in enumerate(records):
            header = minute_record["header"]
            minute_times.append(self._build_minute_time(header))

            for n in minute_names:
                minute_values[n].append(header[n])

            for set_record in minute_record["data"]:
                output_type = set_record["output_type"]

                if output_type in {"B", "S", "O"}:
                    minute_index_per_bs.append(m_idx)
                    bs_times.append(self._build_time(header, set_record["bs_second_of_minute"]))
                    bs_output_types.append(output_type)

                    for n in bs_names:
                        bs_values[n].append(set_record[n])

                else:
                    minute_index_per_d.append(m_idx)
                    d_times.append(self._build_time(header, set_record["d_second_of_minute"]))
                    d_output_types.append(output_type)

                    for n in d_names:
                        d_values[n].append(set_record[n])

        ds = xr.Dataset(
            coords={
                "minute": ("minute", np.arange(len(records), dtype=np.int64)),
                "minute_time": ("minute", minute_times),
                "setBS": ("setBS", bs_times),
                "minute_index_bs": ("setBS", minute_index_per_bs),
                "setD": ("setD", d_times),
                "minute_index_d": ("setD", minute_index_per_d),
            }
        )

        for n in minute_names:
            ds[n] = ("minute", minute_values[n])

        for n in bs_names:
            ds[n] = ("setBS", bs_values[n])

        for n in d_names:
            ds[n] = ("setD", d_values[n])

        ds["bs_output_type"] = ("setBS", bs_output_types)
        ds["d_output_type"] = ("setD", d_output_types)

        first_header = records[0]["header"]

        ds.attrs["source_file"] = str(self.filepath)
        ds.attrs["spacecraft_id"] = first_header.get("spacecraft_id")
        ds.attrs["data_file_id"] = first_header.get("data_file_id")
        ds.attrs["minute_count"] = len(records)
        ds.attrs["bs_record_count"] = len(bs_times)
        ds.attrs["d_record_count"] = len(d_times)
        ds.attrs["record_count"] = len(bs_times) + len(d_times)

        self._apply_schema_attrs(ds, minute_schema)
        self._apply_schema_attrs(ds, EP_BS_SCHEMA)
        self._apply_schema_attrs(ds, EP_D_SCHEMA)

        ds["minute_time"].attrs["long_name"] = "Date and time for the minute"
        ds["setBS"].attrs["long_name"] = "Coordinate for B/S type sets"
        ds["setD"].attrs["long_name"] = "Coordinate for D type sets"
        ds["minute_index_bs"].attrs["long_name"] = "Link between minute and B/S set"
        ds["minute_index_d"].attrs["long_name"] = "Link between minute and D set"
        ds["minute"].attrs["long_name"] = "Coordinate for minutes"
        ds["bs_output_type"].attrs["long_name"] = "Output type for BS records"
        ds["d_output_type"].attrs["long_name"] = "Output type for D records"

        return ds

    def _to_flat_dataframe(self, ds: xr.Dataset) -> pd.DataFrame:
        minute_vars = [name for name in ds.data_vars if "minute" in ds[name].dims]
        minute_df = pd.DataFrame({name: ds[name].values for name in minute_vars})
        minute_df["minute_index"] = np.arange(ds.sizes["minute"], dtype=np.int64)

        bs_vars = [name for name in ds.data_vars if "setBS" in ds[name].dims and name != "bs_output_type"]
        bs_df = pd.DataFrame({name: ds[name].values for name in bs_vars})
        bs_df["minute_index"] = ds["minute_index_bs"].values
        bs_df["output_type"] = ds["bs_output_type"].values

        d_vars = [name for name in ds.data_vars if "setD" in ds[name].dims and name != "d_output_type"]
        d_df = pd.DataFrame({name: ds[name].values for name in d_vars})
        d_df["minute_index"] = ds["minute_index_d"].values
        d_df["output_type"] = ds["d_output_type"].values

        set_df = pd.concat([bs_df, d_df], ignore_index=True, sort=False)

        flat = minute_df.merge(set_df, on="minute_index", how="left")
        flat = flat.drop(columns=["minute_index"])

        spacecraft_id = ds.attrs.get("spacecraft_id")
        data_file_id = ds.attrs.get("data_file_id")

        flat.insert(0, "data_file_id", data_file_id)
        flat.insert(0, "spacecraft_id", spacecraft_id)

        cols = [c for c in flat.columns if c != "output_type"] + ["output_type"]
        flat = flat[cols]

        return flat

    def export_csv(self, ds: xr.Dataset, path: str | Path) -> None:
        flat = self._to_flat_dataframe(ds)
        flat.to_csv(path, index=False)