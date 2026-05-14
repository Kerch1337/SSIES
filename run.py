from ssies import hello
from ssies import DM
from pathlib import Path

print(hello())

parser = DM("f09dm92mar13.dat.gz")
data = parser.parse_file()
print(data)

#print(len(data))