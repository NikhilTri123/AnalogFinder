import xarray as xr

variable = "rhum"  # variable to be coarsened

# dictionary for conversions
varDict = {"sst": "sst", "slp": "msl", "hgt": "z", "uwnd850": "u", "uwnd200": "u", "rhum": "r", "uwndU": "u"}

# paths for original data and coarse data
variableFile = 'C:/Users/Ketan Trivedi/Desktop/Nikhil/variablefiles/' + variable + 'Era.nc'
coarseFile = 'C:/Users/Ketan Trivedi/Desktop/Nikhil/variablefiles/' + variable + 'EraLowRes.nc'

# open variable dataset, coarsen lat/lon, saved coarse data to coarseFile
dataset = xr.open_dataset(variableFile)
data = dataset[varDict[variable]]
print(data)
coarseData = data[::, ::, ::8, ::8]
print(coarseData)
coarseData.to_netcdf(coarseFile)
