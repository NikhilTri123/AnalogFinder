import xarray as xr
import numpy as np
import copy as cp

variables = ["sst", "hgtmid", "shummid", "mslp", "uwndup"]  # variables to be included in analog set
hindcastYears = range(2023, 2024)  # all years to hindcast
month = 7  # stores month that is used for each variable
possAnalogs = range(1970, 2024)  # stores years that can be considered as analogs
analogThresh = 5  # number of analogs in the set

# print on same line and dictionary for conversions
np.set_printoptions(suppress=True)
varDict = {"sst": "sst", "mslp": "msl", "hgtmid": "z", "shummid": "q", "uwndup": "u"}


def createDataset(path, variable):
    """
    Creates a xarray DataArray for the given variable
    :param path: the file path for the netcdf variable file
    :param variable: the variable that the dataset will be made for
    :return: the xarray DataArray for the variable
    """
    dataset = xr.open_dataset(path)
    data = dataset[varDict[variable]]
    return data


def climoSet(data, period, month):
    """
    gets the variable data for the given month in the given period
    :param data: the variable data to be used
    :param period: the period of time that data is retrieved for
    :param month: the month that data is retrieved for
    :return: a list with each element being a year of data in the period
    """
    month = format(month, '02d')
    years = []
    for year in period:
        date = np.datetime64(str(year) + '-' + str(month), 'D')
        years.append(data.sel(time=date))
    return years


def zscoreThing(data, years, month, calcYear):
    """
    Calculates a z-score map for the given month and year
    :param data: the variable data to be used
    :param years: the list of years that z-scores mean/stdev are based off
    :param month: the month that data is calculated for
    :param calcYear: the year that data is calculated for
    :return: a z-score map for the given month and year
    """
    allMeans = np.mean(np.array(years), axis=0)
    allStds = np.std(np.array(years), axis=0)

    month = format(month, '02d')
    date = np.datetime64(str(calcYear) + '-' + str(month), 'D')
    calcYearData = data.sel(time=date)

    allZScores = (calcYearData - allMeans) / allStds
    allZScores = allZScores - np.mean(allZScores)
    return allZScores


def normalize(toNormalize):
    """
    Normalizes an array of data
    :param toNormalize: the array of data to be normalized
    :return: normalized array of data
    """
    minValue = np.min(toNormalize)
    maxValue = np.max(toNormalize)
    varRange = maxValue - minValue
    normalized = (toNormalize - minValue) / varRange
    return normalized


def compareYears(data, yearsList, year, month, corrData):
    """
    Compares the given year to each possible analog year to see how big the differences are between each of them
    :param data: xarray DataArray for a variable
    :param yearsList: the list of years data in the climo period
    :param year: the year to calculate analogs for
    :param month: the month that each global mean anomaly will be calculated for
    :param corrData: the correlation map that goes with the variable and month
    :return: a list containing total differences for each possible analog year
    """
    currAnoms = zscoreThing(data, yearsList, month, year)
    allDiffs = []
    for possAnalog in possAnalogs:
        possAnalogAnoms = zscoreThing(data, yearsList, month, possAnalog)
        difference = currAnoms - possAnalogAnoms
        difference = np.multiply(difference, np.cos(np.radians(difference.latitude)))
        difference = np.multiply(difference, corrData)
        allDiffs.append([possAnalog, float(np.sum(abs(difference)))])
    return allDiffs


def getNumAnalogs(thresh):
    temp = cp.deepcopy(totalAnalogSet)
    allTopFive = []
    for hindYear in temp:
        topFive = []
        num = 1
        while num < len(hindYear) and num < thresh + 1:
            topFive.append(list(hindYear[num]))
            num += 1
        allTopFive.append(topFive)
    return allTopFive


allCorrs = []
corrWeights = []
totalAnalogSet = []

for var in range(len(variables)):
    # set up ACE correlations data
    corrPath = 'C:/Nikhil Stuff/Coding Stuff/variablefiles/NAcorrs/' + variables[var] + 'EraCorr.nc'
    corrDataset = xr.open_dataset(corrPath)
    currMonth = format(month, '02d')
    date = np.datetime64('1969-' + currMonth + '-01', 'D')
    correlations = corrDataset.allAce.sel(time=date)
    correlations = np.multiply(correlations, np.cos(np.radians(correlations.latitude)))

    # put correlations and their overall weights into arrays
    allCorrs.append(correlations)
    corrWeights.append(np.mean(abs(correlations.to_numpy())))
print("correlation weights: " + str(corrWeights))

# loop through hindcastYears to provide analogs for each of those years
for hindcastYear in hindcastYears:
    analogSet = []  # stores analog set for each variable

    # loop through each variable
    for var in range(len(variables)):
        # get climo map for the given month
        varPath = 'C:/Nikhil Stuff/Coding Stuff/variablefiles/' + variables[var] + 'EraModified.nc'
        varData = createDataset(varPath, variables[var])
        yearsClimo = climoSet(varData, possAnalogs, month)

        # get scores for each potential analog and normalize them
        diffList = compareYears(varData, yearsClimo, hindcastYear, month, allCorrs[var])
        diffList = np.array(diffList)
        diffList[:, 1] = normalize(diffList[:, 1])
        analogSet.append(diffList)  # each element is a diffList for a given variable

    # weight each variable's analogs based on corrWeight
    analogSet = np.array(analogSet)
    corrWeights = np.array(corrWeights)
    analogSet[:, :, 1] = np.multiply(analogSet[:, :, 1], corrWeights[:, None])

    # add up differences for each year and sort them into a final list of analogs
    analogSet[0, :, 1] = np.sum(analogSet[:, :, 1], axis=0)
    finalList = analogSet[0]
    finalList = finalList[finalList[:, 1].argsort()]

    # store the sorted analog list and move onto the next hindcast year
    totalAnalogSet.append(finalList)
    print(hindcastYear, end=" ")
print()

print(((1 - normalize(np.array(totalAnalogSet)[:, :, 1])) * 100).tolist())
topAnalogs = getNumAnalogs(analogThresh)
startYear = hindcastYears[0]
for hindcastYear in np.array(topAnalogs)[:, :, 0].astype(int).tolist():
    print(str(startYear) + ": " + str(hindcastYear))
    startYear += 1
