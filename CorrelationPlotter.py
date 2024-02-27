import xarray as xr
import numpy as np
import cartopy.crs as ccrs
import cartopy.feature as cf
import matplotlib.pyplot as plt

variables = ["sst", "slp", "hgt", "uwnd850", "uwnd200", "rhum", "vrt850"]
month = 7
displayVar = "sst"


def createCorrDataset(path, month):
    """
    Creates a xarray dataset for the given variable correlation
    :param path: the file path for the netcdf variable file
    :param month: month that the correlation map is calculated for
    :return: the xarray dataset for the variable correlation
    """
    dataset = xr.open_dataset(path)
    month = format(month, '02d')
    date = np.datetime64('1969-' + month, 'D')
    data = dataset.allAce.sel(time=date)
    return data


# dictionary for conversions
monthsDict = {1: "January", 2: "February", 3: "March", 4: "April", 5: "May", 6: "June", 7: "July", 8: "August",
              9: "September", 10: "October", 11: "November", 12: "December"}

allCorrData = []
for var in variables:
    # open each variable correlation file for the given month
    varPath = 'C:/Users/Ketan Trivedi/Desktop/Nikhil/variablefiles/NAcorrs/' + var + 'EraCorr.nc'
    corrData = createCorrDataset(varPath, month)

    # low high-latitude weighting and print overall correlation
    corrData = np.multiply(corrData, np.cos(np.radians(corrData.latitude)))
    print(var + ": " + str(round(np.average(np.abs(corrData)), 4)))
    allCorrData.append(corrData)

# display the variable chosen above
corrDisplay = allCorrData[variables.index(displayVar)]

# plot cartopy map and various features
ax = plt.axes(projection=ccrs.PlateCarree(central_longitude=180))
ax.coastlines(linewidth=0.5, resolution='50m')
ax.add_feature(cf.BORDERS, linewidth=0.3)
ax.add_feature(cf.STATES, linewidth=0.2, edgecolor="gray")
ax.add_feature(cf.LAND)

# add data, colormap, and title
plt.contourf(corrDisplay.longitude, corrDisplay.latitude, corrDisplay, np.arange(-1, 1, 0.02), extend='both',
             transform=ccrs.PlateCarree())
plt.set_cmap('RdBu_r')
mainTitle = "ERA5 " + str(monthsDict[month]) + " SST's Correlated to Atlantic ACE"
plt.title(mainTitle, fontsize=7, weight='bold', loc='left')
plt.title("DCAreaWx", fontsize=7, weight='bold', loc='right', color='gray')

# add colorbar and set ticks
cbar = plt.colorbar(orientation='horizontal', pad=0.04, aspect=50)
cbar.set_ticks([-1, -0.5, 0, 0.5, 1])
cbar.ax.tick_params(labelsize=7)

# save and display map
plt.savefig(r"C:/Users/Ketan Trivedi/Desktop/Nikhil/sstMap" + str(month) + ".png", dpi=300, bbox_inches='tight')
plt.show()
