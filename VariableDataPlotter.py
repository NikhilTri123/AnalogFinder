import xarray as xr
import numpy as np
import cartopy.crs as ccrs
import cartopy.feature as cf
import matplotlib.pyplot as plt


variable = "sst"
analogYears = [2020, 1998, 2021, 2010]
month = 5

# dictionaries for conversions
varDict = {"sst": "sst", "slp": "msl", "hgt": "z", "uwnd200": "u", "uwnd850": "u"}
monthsDict = {1: "January", 2: "February", 3: "March", 4: "April", 5: "May", 6: "June", 7: "July", 8: "August",
              9: "September", 10: "October", 11: "November", 12: "December"}


def calcClimo(data, period, month):
    """
    Calculates a global climo map during the given period for the given month(s)
    :param data: xarray DataArray for a variable
    :param period: range of years that will be averaged
    :param month: month that the climo period is generated for
    :return: a global climo map
    """
    month = format(month, '02d')
    years = []
    for year in period:
        date = np.datetime64(str(year) + '-' + str(month), 'D')
        years.append(data.sel(time=date))
    climo = sum(years) / len(years)
    return climo


def calcGlobeMeanAnom(data, climo, year, month):
    """
    Calculates a global mean anomaly map for the given year and month(s) using the given climo period
    :param data: xarray DataArray for a variable
    :param climo: the climo period map being used
    :param year: the year that the anomaly will be calculated for
    :param month: the month that the anomaly will be calculated for
    :return: a global mean anomaly map
    """
    current = calcClimo(data, [year], month)
    anomaly = current - climo
    globeMeanAnom = anomaly - np.mean(anomaly)
    return globeMeanAnom


# open variable data
varPath = 'D:/Nikhil/variablefiles/' + variable + 'EraLowRes1.nc'
varDataset = xr.open_dataset(varPath)
varData = varDataset[varDict[variable]]

# get anomaly data for top 5 analogs and average them out
anoms = []
for year in analogYears:
    climo = calcClimo(varData, range(1991, 2021), month)
    anoms.append(calcGlobeMeanAnom(varData, climo, year, month))
anom = sum(anoms) / len(anoms)

# plot cartopy map and various features
ax = plt.axes(projection=ccrs.PlateCarree(central_longitude=180))
ax.coastlines(linewidth=0.5, resolution='50m')
ax.add_feature(cf.BORDERS, linewidth=0.3)
ax.add_feature(cf.STATES, linewidth=0.2, edgecolor="gray")
ax.add_feature(cf.LAND)

# add data, colormap, and title
plt.contourf(anom.longitude, anom.latitude, anom, np.arange(-1, 1, 0.02), extend='both', transform=ccrs.PlateCarree())
plt.set_cmap('RdBu_r')
mainTitle = "ERA5 " + str(monthsDict[month]) + " Global Mean SSTA For Top 5 Analogs"
plt.title(mainTitle + "\nYears: " + str(analogYears), fontsize=7, weight='bold', loc='left')
plt.title("DCAreaWx", fontsize=7, weight='bold', loc='right', color='gray')

# add colorbar and set ticks
cbar = plt.colorbar(orientation='horizontal', pad=0.04, aspect=50)
cbar.set_ticks([-1, -0.5, 0, 0.5, 1])
cbar.ax.tick_params(labelsize=7)

# save and display map
plt.savefig(r"D:/Nikhil/VarAnomMap.png", dpi=300, bbox_inches='tight')
plt.show()
