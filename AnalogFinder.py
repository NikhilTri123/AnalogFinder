import xarray as xr
import numpy as np
from scipy.stats import pearsonr
import cartopy.crs as ccrs
import cartopy.feature as cf
import matplotlib.pyplot as plt
import AceCalculator

variables = ["sst", "uwndup", "uwndlow", "stab"]  # variables to be included in analog set
year = 2012  # year to calculate analogs for
months = range(1, 10)  # stores month that is used for each variable
possAnalogs = range(1970, 2024)  # stores years that can be considered as analogs
analogThresh = 7  # number of analogs in the set

# dictionary for conversions
varDict = {"sst": "sst", "mslp": "msl", "hgtmid": "z", "shummid": "q", "uwndup": "u", "uwndlow": "u", "stab": "ss"}


def zscoreThing(data):
    """
    Normalizes variable data to account for different amounts of variability in different regions
    :param data: the variable DataArray to be normalized
    :return: the normalized variable DataArray
    """
    # calculate mean/standard deviation maps for each month
    month_groups = data.groupby('time.month')
    allMeans = month_groups.mean(dim='time')
    allStds = month_groups.std(dim='time')

    # use appropriate mean/std maps to calculate z-score map for each time
    month_zscores = []
    for mon in set(data['time.month'].to_numpy()):
        mask = data['time.month'] == mon
        zscoreMap = (data.sel(time=mask) - allMeans.sel(month=mon)) / allStds.sel(month=mon)
        month_zscores.append(zscoreMap.drop_vars('month'))

    # concat z-score data for each month and return
    zscore_data = xr.concat(month_zscores, dim='time')
    return zscore_data


currDataList, analogDataList, corrDataList = [], [], []  # stores analog set for each variable

# loop through each variable
for var in range(len(variables)):
    # get climo map for the given month
    varPath = 'C:/Nikhil Stuff/Coding Stuff/variablefiles/' + variables[var] + 'EraModified.nc'
    varDataset = xr.open_dataset(varPath)
    varData = varDataset[varDict[variables[var]]]
    varData = zscoreThing(varData)

    corrPath = 'C:/Nikhil Stuff/Coding Stuff/variablefiles/NAcorrs/' + variables[var] + 'EraCorr.nc'
    corrDataset = xr.open_dataset(corrPath)
    corrMask = (corrDataset['time.month'] >= months[0]) & (corrDataset['time.month'] <= months[-1])
    corrData = corrDataset.allAce.sel(time=corrMask)
    corrData = np.multiply(corrData, np.cos(np.radians(corrData.latitude)))
    corrDataList.append(corrData)

    monthMask = (varData['time.month'] >= months[0]) & (varData['time.month'] <= months[-1])
    yearMask = (varData['time.year'] >= possAnalogs[0]) & (varData['time.year'] <= possAnalogs[-1])

    currData = varData.sel(time=(varData["time.year"] == year) & monthMask)
    currData = np.multiply(currData, np.cos(np.radians(currData.latitude)))
    currDataList.append(currData)

    analogData = varData.sel(time=yearMask & monthMask)
    analogData = np.multiply(analogData, np.cos(np.radians(analogData.latitude)))
    analogDataList.append(analogData)

corrFlat = np.array(corrDataList).flatten()
currFlat = np.array(currDataList).flatten()
currFlat = np.nan_to_num(currFlat)

scores = []
for possAnalog in possAnalogs:
    analogData = np.array([var.sel(time=var['time.year'] == possAnalog) for var in analogDataList])
    analogFlat = analogData.flatten()
    analogFlat = np.nan_to_num(analogFlat)

    # calculate correlation between maps and append to scores
    correlation = pearsonr(analogFlat, currFlat)[0]
    scores.append([possAnalog, correlation])

# add up differences for each year and sort them into a final list of analogs
scores = np.array(scores)
scores = scores[np.flip(scores[:, 1].argsort())]
scores[:, 1] = np.round(scores[:, 1], 3)
if year != 2024:
    scores = scores[1:]

# store the sorted analog list and move onto the next hindcast year
scores = scores[scores[:, 1] >= 0]
print(f"{year}: {scores.tolist()}")

# get hurdat data from 1851-present
allHurdatData = AceCalculator.getHurdatData('C:/Nikhil Stuff/Coding Stuff/hurdatdata.txt')
allHurdatData = [storm[1] for storm in allHurdatData]

diffHists = []
for analog in scores[:, 0]:
    # store data for coordinates and ACE for all years and analog years in lists
    allX, allY, allAce = [], [], []
    analogX, analogY, analogAce = [], [], []

    # loop through every line of data
    for storm in allHurdatData:
        for stormData in storm:
            # only include data if it meets the requirements for ACE calculation
            if stormData[1] in ['0000', '0600', '1200', '1800'] and stormData[3] in ['TS', 'HU', 'SS'] \
                    and int(stormData[6]) >= 34 and int(stormData[0][:4]) >= 1970:
                allX.append(float(stormData[5][:-1]) * -1)
                allY.append(float(stormData[4][:-1]))
                allAce.append(int(stormData[6]) * int(stormData[6]) / 10000)

                # append to analog lists if the data falls under one of those years
                if int(stormData[0][:4]) == analog:
                    analogX.append(float(stormData[5][:-1]) * -1)
                    analogY.append(float(stormData[4][:-1]))
                    analogAce.append(int(stormData[6]) * int(stormData[6]) / 10000)

    # calculate histograms for all data and analog data and then subtract to get the anomaly
    allHist2d = np.histogram2d(allX, allY, bins=[20, 10], weights=allAce, range=([-120, 0], [0, 60]))
    analogHist2d = np.histogram2d(analogX, analogY, bins=[20, 10], weights=analogAce, range=([-120, 0], [0, 60]))
    diffHist = analogHist2d[0] - allHist2d[0] / 54
    diffHists.append(diffHist)

scores[:, 1] /= sum(scores[:, 1])
diffHists = np.array(diffHists)
diffHist = np.average(diffHists, axis=0, weights=scores[:, 1])

# plot cartopy map and various features
plt.figure(figsize=(12, 6))
ax = plt.axes(projection=ccrs.PlateCarree())
ax.add_feature(cf.LAND)
ax.add_feature(cf.STATES, linewidth=0.2, edgecolor="gray")
ax.add_feature(cf.BORDERS, linewidth=0.3)
ax.coastlines(linewidth=0.5, resolution='50m')

# plot gridlines
gl = ax.gridlines(crs=ccrs.PlateCarree(central_longitude=0), draw_labels=True, linewidth=1, color='gray', alpha=0.5,
                  linestyle='--')
gl.top_labels = gl.right_labels = False
gl.xlabel_style = {'size': 7, 'weight': 'bold', 'color': 'gray'}
gl.ylabel_style = {'size': 7, 'weight': 'bold', 'color': 'gray'}

# add data and colormap
plt.imshow(diffHist.T, interpolation='gaussian', cmap='RdBu_r', origin='lower', extent=[-120, 0, 0, 60],
           vmin=-3, vmax=3)
ax.set_extent([-100, -5, 5, 50])
cbar = plt.colorbar(pad=0.015, aspect=27, shrink=0.99, extend='both')
cbar.ax.tick_params(labelsize=7)

mainTitle = f"Weighted ACE Density Anomaly of All Analogs"
plt.title(f"{mainTitle} \nYear: {year}", fontsize=9, weight='bold', loc='left')
plt.title("DCAreaWx", fontsize=9, weight='bold', loc='right', color='gray')

plt.savefig(r"C:/Nikhil Stuff/Coding Stuff/AceAnomMap.png", dpi=300, bbox_inches='tight')
plt.show()
