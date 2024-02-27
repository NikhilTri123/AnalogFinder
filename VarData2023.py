import xarray as xr

variable = "uwnd850"

# paths for pre-2023 data, 2023 data, and merged data
oldFilePath = 'C:/Users/Ketan Trivedi/Desktop/Nikhil/variablefiles/' + variable + 'EraLowRes.nc'
newFilePath = 'C:/Users/Ketan Trivedi/Desktop/Nikhil/variablefiles/' + variable + '2023EraLowRes.nc'
mergedFilePath = 'C:/Users/Ketan Trivedi/Desktop/Nikhil/variablefiles/' + variable + 'EraLowRes1.nc'

# open dataset of pre-2023 variable data
oldDataset = xr.open_dataset(oldFilePath)

# open dataset of 2023 variable data and remove expver coordinate
newDataset = xr.open_dataset(newFilePath)
newDataset1 = newDataset.sel(expver=1, time=slice("2023-01-01", "2023-02-01"))
newDataset2 = newDataset.sel(expver=5, time=slice("2023-03-01", "2023-04-01"))
newDataset = xr.concat([newDataset1, newDataset2], dim="time")
newDataset = newDataset.drop_vars("expver")

# append 2023 dataset to pre-2023 dataset and save to files
mergedDataset = xr.concat([oldDataset, newDataset], dim="time")
mergedDataset.to_netcdf(mergedFilePath)
print(mergedDataset)
