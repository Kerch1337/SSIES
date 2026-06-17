# SSIES

Python library for parsing data files SSIES detector DMSP project.

Description of library capabilities:
1) Reading compressed binary files from the SSIES detector.
2) Converting data from binary SSIES detector files into data with measurable physical quantities.
3) Extracting and processing headers and timestamps—metadata in files.
4) Correct organization of the structure and metadata in exported files to enable automated data analysis and their correct interpretation in scientific tools such as Panoply.
5) Exporting converted data to convenient formats: NetCDF and CSV.

The ssies package provides five classes (DM, EP, MP, RPA, SM) for five different datasets. These classes have similar methods and functionality. However, each class only works with files containing specific datasets.

# API Reference for each class

| Method | Input | Output |
|---------|---------|---------|
| `parse_file()` | File path (provided when creating the parser instance) | `xarray.Dataset` |
| `export_netcdf()` | `xarray.Dataset`, output filename | NetCDF file (`.nc`) saved to the project root |
| `export_csv()` | `xarray.Dataset`, output filename | CSV file (`.csv`) saved to the project root |

# Installation
`pip install ssies`

# Example

`from ssies import DM`

`parser = DM("f13dm09nov05.dat.gz")`   
`ds = parser.parse_file()`

`print(ds)`

## Export to CSV:

`parser.export_csv(ds, "output.csv")`

## Export to NetCDF:

`parser.export_netcdf(ds, "output.nc")`