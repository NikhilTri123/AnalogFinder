import AceCalculator
import numpy as np
import cartopy.crs as ccrs
import cartopy.feature as cf
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

analogYears = [1998, 2010]  # years to plot ACE density anomaly map for

# get hurdat data from 1851-present
allHurdatData = AceCalculator.getHurdatData('C:/Nikhil Stuff/Coding Stuff/hurdatdata.txt')
allHurdatData = [storm[1] for storm in allHurdatData]

# store data for coordinates and ACE for all years and analog years in lists
allX, allY, allAce = [], [], []
analogX, analogY, analogAce = [], [], []

# loop through every line of data
for storm in allHurdatData:
    for stormData in storm:
        # only include data if it meets the requirements for ACE calculation
        if stormData[1] in ['0000', '0600', '1200', '1800'] and stormData[3] in ['TS', 'HU', 'SS'] \
                and int(stormData[6]) >= 34:
            stormData = np.array(stormData)
            allX.append(float(stormData[5][:-1]) * -1)
            allY.append(float(stormData[4][:-1]))
            allAce.append(int(stormData[6]) * int(stormData[6]) / 10000)

            # append to analog lists if the data falls under one of those years
            if int(stormData[0][:4]) in analogYears:
                analogX.append(float(stormData[5][:-1]) * -1)
                analogY.append(float(stormData[4][:-1]))
                analogAce.append(int(stormData[6]) * int(stormData[6]) / 10000)

# calculate histograms for all data and analog data and then subtract to get the anomaly
allHist2d = np.histogram2d(allX, allY, bins=20, density=True, weights=allAce, range=([-120, 0], [0, 60]))
analogHist2d = np.histogram2d(analogX, analogY, bins=20, density=True, weights=analogAce, range=([-120, 0], [0, 60]))
diffHist = analogHist2d[0] - allHist2d[0]

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
           norm=mcolors.TwoSlopeNorm(0))
ax.set_extent([-100, -5, 5, 50])
cbar = plt.colorbar(pad=0.015, aspect=27, shrink=0.99, extend='both')
# cbar.set_ticks(np.arange(-0.0015, 0.0015, 0.0005))
cbar.ax.tick_params(labelsize=7)

mainTitle = "ACE Density Anomaly of Top Analogs"
plt.title(mainTitle + "\nYears: " + str(analogYears), fontsize=9, weight='bold', loc='left')
plt.title("DCAreaWx", fontsize=9, weight='bold', loc='right', color='gray')

plt.savefig(r"C:/Nikhil Stuff/Coding Stuff/AceAnomMap.png", dpi=300, bbox_inches='tight')
plt.show()
