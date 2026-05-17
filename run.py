from ssies import DM, MP, RPA, SM, EP
from pathlib import Path

"""parser = MP("f14mp08aug23.dat.gz")
ds = parser.parse_file()
print(ds)
parser.export_netcdf(ds, "mp.nc")
parser.export_csv(ds, "mp.csv")

#print(len(data))

#print(ds.attrs)

#for var in ds.data_vars:
#    print(var, ds[var].attrs)

parser2 = DM("f09dm92mar13.dat.gz")
ds2 = parser2.parse_file()
print(ds2)
parser2.export_netcdf(ds2, "dm.nc")
parser2.export_csv(ds2, "dm.csv")

parser3 = RPA("f15rp15dec05.dat.gz")
ds3 = parser3.parse_file()
print(ds3)
parser3.export_netcdf(ds3, "rpa.nc")
parser3.export_csv(ds3, "rpa.csv")

parser4 = SM("f15sm16jun06.dat.gz")
ds4 = parser4.parse_file()
print(ds4)
parser4.export_netcdf(ds4, "sm.nc")
parser4.export_csv(ds4, "sm.csv")"""


parser5 = EP("f08ep88jan09.dat.gz")
ds5 = parser5.parse_file()
print(ds5)
#print(ds5.attrs)
#for var in ds5.data_vars:
#   print(var, ds5[var].attrs)
parser5.export_netcdf(ds5, "ep.nc")
parser5.export_csv(ds5, "ep.csv")