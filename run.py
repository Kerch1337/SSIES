from ssies import hello
from ssies import DM
from pathlib import Path

print(hello())

parser = DM("f09dm92mar13.dat.gz")
data = parser.parse_file()
ds = parser.to_xarray(data)

#parser.export_netcdf(ds, "out.nc")
#parser.export_cdf(ds, "out.cdf")
parser.export_csv(ds, "out.csv")

#print(ds)

#print(len(data))

#print(ds.attrs)

#for var in ds.data_vars:
#    print(var, ds[var].attrs)