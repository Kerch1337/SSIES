from pathlib import Path
import gzip
import math

from pathlib import Path
import gzip
import math


class SSIES:

    def __init__(self, filepath):

        self.filepath = Path(filepath)

    def _open_file(self):

        if self.filepath.suffix.lower() == ".gz":

            return gzip.open(
                self.filepath,
                "rb"
            )

        return open(
            self.filepath,
            "rb"
        )

    def _read_exact(self, file, size):

        data = file.read(size)

        if len(data) != size:

            raise EOFError(
                f"Expected {size} bytes, got {len(data)}."
            )

        return data

    def _all_bytes_equal(self, data, value):

        return all(
            byte == value
            for byte in data
        )

    def _read_uint(self, file, size):

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

    def _read_ascii(self, file, size):

        raw = self._read_exact(
            file,
            size
        )

        return raw.decode(
            "ascii"
        ).rstrip()

    def _read_bytes(self, file, size):

        return self._read_exact(
            file,
            size
        )

    def _parse_schema(self, file, schema):

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
                value = transform(value)

            result[name] = value

        return result