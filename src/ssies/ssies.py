from pathlib import Path
import gzip
import math
import datetime as dt
import xarray as xr


class SSIES:

    def __init__(self, filepath: str | Path) -> None:

        self.filepath = Path(filepath)

    def _open_file(self) -> gzip.GzipFile:

        return gzip.open(
            self.filepath,
            "rb"
        )

    def _read_exact(self, file: gzip.GzipFile, size: int) -> bytes:

        data = file.read(size)

        if len(data) != size:

            raise EOFError(
                f"Expected {size} bytes, but got {len(data)}."
            )

        return data

    def _all_bytes_equal(self, data: bytes, value: int) -> bool:

        return all(
            byte == value
            for byte in data
        )

    def _read_uint(self, file: gzip.GzipFile, size: int) -> int | float:

        raw = self._read_exact(
            file,
            size
        )

        if self._all_bytes_equal(raw, 0xFF):

            return math.nan

        value = int.from_bytes(
            raw,
            byteorder="big",
            signed=False
        )

        return value

    def _read_ascii(self, file: gzip.GzipFile, size: int) -> str:

        raw = self._read_exact(
            file,
            size
        )

        return raw.decode(
            "ascii"
        ).rstrip()

    def _read_bytes(self, file: gzip.GzipFile, size: int) -> bytes:

        return self._read_exact(
            file,
            size
        )

    def _parse_schema(self, file: gzip.GzipFile, schema: list[dict]) -> dict:

        result = {}

        for field in schema:

            name = field["name"]

            size = field["size"]

            field_type = field["type"]

            transform = field.get(
                "transform"
            )

            if field_type == "ascii":

                value = self._read_ascii(
                    file,
                    size
                )

            elif field_type == "uint":

                value = self._read_uint(
                    file,
                    size
                )

            elif field_type == "bytes":

                value = self._read_bytes(
                    file,
                    size
                )

            else:

                raise ValueError(
                    f"Unsupported type: {field_type}"
                )

            if transform is not None and not (isinstance(value, float) and math.isnan(value)):
                try:
                    value = transform(value)
                except Exception:
                    value = math.nan

            result[name] = value

        return result

    def _resync_to_next_header(self, file: gzip.GzipFile, header_scheme: list[dict]) -> bool:
        max_search = 5000

        while max_search > 0:
            start_offset = file.tell()
            max_search -= 1

            try:
                candidate = self._parse_schema(file, header_scheme)

                if self._is_valid_header(candidate):
                    file.seek(start_offset)
                    return True

            except EOFError:
                return False

            except (UnicodeDecodeError, Exception):
                file.seek(start_offset + 1)
                continue

            file.seek(start_offset + 1)

        return False

    def _is_valid_header(self, header: dict) -> bool:
        return False

    def _parse_minute_record(self, file: gzip.GzipFile, header_scheme: list[dict], set_scheme: list[dict], field_name: str) -> dict:

        start_offset = file.tell()

        header = self._parse_schema(
            file,
            header_scheme
        )

        if not self._is_valid_header(header):
            raise ValueError(
                f"Invalid MP header at offset {start_offset}: {header}"
            )

        number_set = header[field_name]
        data = []

        for _ in range(number_set):
            set_record = self._parse_schema(
                file,
                set_scheme
            )
            data.append(set_record)

        return {
            "header": header,
            "data": data,
        }

    def _build_minute_time(self, header: dict) -> dt.datetime:
        return dt.datetime(
            int(header["year"]),
            1,
            1,
            int(header["hour"]),
            int(header["minute_of_hour"]),
        ) + dt.timedelta(days=int(header["day_of_year"]) - 1)

    def _build_time(self, header: dict, second_of_minute: int | float) -> dt.datetime:
        return self._build_minute_time(header) + dt.timedelta(
            seconds=int(second_of_minute)
        )

    def export_netcdf(self, ds: xr.Dataset, path: str | Path) -> None:
        ds.to_netcdf(path, format="NETCDF4")

    def _apply_schema_attrs(self, ds: xr.Dataset, schema: list[dict]) -> xr.Dataset:
        for field in schema:
            name = field["name"]

            if name in ds:
                if field.get("units") is not None:
                    ds[name].attrs["units"] = field["units"]

                if field.get("long_name") is not None:
                    ds[name].attrs["long_name"] = field["long_name"]

        return ds