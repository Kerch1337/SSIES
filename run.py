from ssies import DM, MP, RPA, SM
from pathlib import Path

"""parser = MP("f14mp08aug23.dat.gz")
data = parser.parse_file()
ds = parser.to_xarray(data)
print(ds)
parser.export_netcdf(ds, "mp.nc")
parser.export_csv(ds, "mp.csv")"""

#print(len(data))

#print(ds.attrs)

#for var in ds.data_vars:
#    print(var, ds[var].attrs)

"""parser2 = DM("f09dm92mar13.dat.gz")
data2 = parser2.parse_file()
ds2 = parser2.to_xarray(data2)
print(ds2)
parser2.export_netcdf(ds2, "dm.nc")
parser2.export_csv(ds2, "dm.csv")"""

"""parser3 = RPA("f15rp15dec05.dat.gz")
data3 = parser3.parse_file()
ds3 = parser3.to_xarray(data3)
print(ds3)
parser3.export_netcdf(ds3, "rpa.nc")
parser3.export_csv(ds3, "rpa.csv")"""

parser4 = SM("f15sm16jun06.dat.gz")
data4 = parser4.parse_file()
ds4 = parser4.to_xarray(data4)
print(ds4)
parser4.export_netcdf(ds4, "sm.nc")
parser4.export_csv(ds4, "sm.csv")