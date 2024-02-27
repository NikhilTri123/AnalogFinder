import xarray as xr

variable = "vrt850"
filePath = 'C:/Users/Ketan Trivedi/Desktop/Nikhil/variablefiles/' + variable + 'Era.nc'
print(xr.open_dataset(filePath))
