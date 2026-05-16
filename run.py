from ssies import DM, MP
from pathlib import Path

parser = MP("f14mp08aug23.dat.gz")
data = parser.parse_file()
ds = parser.to_xarray(data)
print(ds)
parser.export_netcdf(ds, "mp.nc")
parser.export_csv(ds, "mp.csv")

#print(len(data))

#print(ds.attrs)

#for var in ds.data_vars:
#    print(var, ds[var].attrs)

parser2 = DM("f09dm92mar13.dat.gz")
data2 = parser2.parse_file()
ds2 = parser2.to_xarray(data2)
print(ds2)
parser2.export_netcdf(ds2, "dm.nc")
parser2.export_csv(ds2, "dm.csv")