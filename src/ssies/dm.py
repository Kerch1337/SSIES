from .ssies import SSIES
from .schemas import HEADER_SCHEMA, DM_SCHEMA

class DM(SSIES):

    def _is_valid_header(self, header):
        spacecraft_id = header["spacecraft_id"]
        data_file_id = header["data_file_id"]
        seconds_in_minute = header["seconds_in_minute"]

        if data_file_id != "DM":
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

        if not (0 <= header["minute"] <= 59):
            return False

        if not (1 <= seconds_in_minute <= 60):
            return False

        return True

    def _parse_minute_record(self, file):
        start_offset = file.tell()

        header = self._parse_schema(
            file,
            HEADER_SCHEMA
        )

        if not self._is_valid_header(header):
            raise ValueError(
                f"Invalid DM header at offset {start_offset}: {header}"
            )

        seconds_in_minute = header["seconds_in_minute"]
        data = []

        for _ in range(seconds_in_minute):
            second_record = self._parse_schema(
                file,
                DM_SCHEMA
            )
            data.append(second_record)

        return {
            "header": header,
            "data": data,
        }

    def _resync_to_next_header(self, file):
        while True:
            start_offset = file.tell()

            try:
                candidate = self._parse_schema(
                    file,
                    HEADER_SCHEMA
                )
            except (EOFError, UnicodeDecodeError):
                return False

            if self._is_valid_header(candidate):
                file.seek(start_offset)
                return True

            file.seek(start_offset + 1)

    def parse_file(self):
        records = []

        with self._open_file() as file:
            while True:
                try:
                    minute_record = self._parse_minute_record(file)
                    records.append(minute_record)

                except EOFError:
                    break

                except (ValueError, UnicodeDecodeError):
                    if not self._resync_to_next_header(file):
                        break

        return records