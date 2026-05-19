EP_OUTPUT_TYPE_SCHEMA = [
    {
        "name": "output_type",
        "size": 1,
        "type": "ascii",
        "transform": lambda x: x.strip(),
        "units": None,
        "long_name": "Output type for set",
    },
]

EP_BS_SCHEMA = [
    {
        "name": "bs_second_of_minute",
        "size": 1,
        "type": "uint",
        "transform": lambda x: x,
        "units": "second",
        "long_name": "Second of minute",
    },
    {
        "name": "bs_langmuir_probe_mode",
        "size": 1,
        "type": "ascii",
        "transform": lambda x: x.strip(),
        "units": None,
        "long_name": "Langmuir probe mode",
    },
    {
        "name": "bs_electron_density",
        "size": 2,
        "type": "uint",
        "transform": lambda x: round(10 ** (x / 100.0)),
        "units": "cm-3",
        "long_name": "Electron density",
    },
    {
        "name": "bs_spacecraft_potential",
        "size": 2,
        "type": "uint",
        "transform": lambda x: round((x / 10.0) - 35.0, 1),
        "units": "V",
        "long_name": "Spacecraft potential",
    },
    {
        "name": "bs_electron_temperature",
        "size": 2,
        "type": "uint",
        "transform": lambda x: round(10 ** (x / 100.0)),
        "units": "K",
        "long_name": "Electron temperature",
    },
    {
        "name": "bs_zero_fill",
        "size": 1,
        "type": "bytes",
        "transform": lambda x: x,
        "units": None,
        "long_name": "Zero fill",
    },
]


EP_D_SCHEMA = [
    {
        "name": "d_second_of_minute",
        "size": 1,
        "type": "uint",
        "transform": lambda x: x,
        "units": "second",
        "long_name": "Second of minute",
    },
    {
        "name": "d_langmuir_probe_mode",
        "size": 1,
        "type": "ascii",
        "transform": lambda x: x.strip(),
        "units": None,
        "long_name": "Langmuir probe mode",
    },
    {
        "name": "d_mean_electron_density",
        "size": 2,
        "type": "uint",
        "transform": lambda x: round(10 ** (x / 100.0)),
        "units": "cm-3",
        "long_name": "Mean electron density for first 4 seconds of dwell",
    },
    {
        "name": "d_std_dev_electron_density",
        "size": 2,
        "type": "uint",
        "transform": lambda x: round(10 ** (x / 100.0)),
        "units": "cm-3",
        "long_name": "Standard deviation of electron density for first 4 seconds of dwell",
    },
    {
        "name": "d_zero_fill_2",
        "size": 2,
        "type": "bytes",
        "transform": lambda x: x,
        "units": None,
        "long_name": "Zero fill",
    },
    {
        "name": "d_zero_fill_1",
        "size": 1,
        "type": "bytes",
        "transform": lambda x: x,
        "units": None,
        "long_name": "Zero fill",
    },
]