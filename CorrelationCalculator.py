import xarray as xr
import numpy as np
from scipy.stats import pearsonr
import AceCalculator
from multiprocessing import Pool
import time as t

variable = "sst"
aceMonths = [range(1, 13), [1], [2], [3], [4], [5], [6], [7], [8], [9], [10], [11], [12]]
corrYears = list(range(1970, 2023))

# variable path and dictionaries for conversions
varPath = 'C:/Users/Ketan Trivedi/Desktop/Nikhil/variablefiles/' + variable + 'EraLowRes.nc'
varDict = {"sst": "sst", "slp": "msl", "hgt": "z", "vp": "velocity_potential", "stream": "streamfunction", "shum": "q",
           "cape": "cape", "uwnd200": "u"}
monthsDict = {1: "January", 2: "February", 3: "March", 4: "April", 5: "May", 6: "June", 7: "July", 8: "August",
              9: "September", 10: "October", 11: "November", 12: "December", range(1, 13): "all"}


def createDataset(path):
    """
    Creates a xarray DataArray for the given variable
    :param path: the file path for the netcdf variable file
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


def getCorrelation(varDataset, aceVals, varMonth):
    """
    Calculates a global correlation map between a given variable and list of ACE values for a given month. E.g. if the
    variable is SST data, the aceVals are for September only, and the month is June, a correlation map between June
    SST's and September ACE will be calculated
    :param varDataset: xarray dataset for a variable
    :param aceVals: List of ACE values for a given month and time period
    :param varMonth: month that the correlation map is calculated for
    :return: a global correlation map
    """
    # each element in switchedData is a list data from each year for a given pixel
    allYears = climoSet(varDataset, corrYears, varMonth)
    allFlattenedData = np.array([zscoreThing(varDataset, allYears, varMonth, year).values.flatten() for year in
                                 corrYears])
    switchedData = np.nan_to_num(allFlattenedData.T)

    # each element is a correlation for a given pixel
    corrList = np.array([pearsonr(pixelData, aceVals) for pixelData in switchedData])
    corrList = np.where(corrList[:, 1] <= 0.05, corrList[:, 0], 0)

    # list of correlations is reshaped to map of correlations
    corrList = np.reshape(corrList, varDataset.shape[1:])
    corrList = np.nan_to_num(corrList)

    return corrList


def main(aceMonth):
    print("Generating correlation map for month " + str(aceMonth))

    # get 1970-present ACE for given month
    yearsAce = np.array(AceCalculator.getMonthAce(aceMonth))
    aceData = yearsAce[:, 1]

    # create dataset for given variable
    varDataset = createDataset(varPath)

    # correlate variable data to ACE for each month of variable data
    corrMonths = np.array([getCorrelation(varDataset, aceData, varMonth) for varMonth in range(1, 13)])
    return corrMonths


if __name__ == '__main__':
    # calculate all correlations in parallel and store them in correlations
    start = t.time()
    with Pool() as pool:
        correlations = pool.map(main, aceMonths)
    print("Finished in " + str(round(t.time() - start)) + " seconds")

    # create and save correlation dataset
    latLonValues = createDataset(varPath)
    time = np.arange('1969-01-01', '1970-01-01', dtype='datetime64[M]')
    ds = xr.Dataset(
        data_vars=dict(
            allAce=(["time", "latitude", "longitude"], correlations[0]),
            janAce=(["time", "latitude", "longitude"], correlations[1]),
            febAce=(["time", "latitude", "longitude"], correlations[2]),
            marAce=(["time", "latitude", "longitude"], correlations[3]),
            aprAce=(["time", "latitude", "longitude"], correlations[4]),
            mayAce=(["time", "latitude", "longitude"], correlations[5]),
            junAce=(["time", "latitude", "longitude"], correlations[6]),
            julAce=(["time", "latitude", "longitude"], correlations[7]),
            augAce=(["time", "latitude", "longitude"], correlations[8]),
            sepAce=(["time", "latitude", "longitude"], correlations[9]),
            octAce=(["time", "latitude", "longitude"], correlations[10]),
            novAce=(["time", "latitude", "longitude"], correlations[11]),
            decAce=(["time", "latitude", "longitude"], correlations[12]),
        ),
        coords=dict(
            time=(["time"], time),
            latitude=(["latitude"], latLonValues.latitude.values),
            longitude=(["longitude"], latLonValues.longitude.values)
        )
    )
    print(ds)
    ds.to_netcdf('C:/Users/Ketan Trivedi/Desktop/Nikhil/variablefiles/NAcorrs/' + variable + 'EraCorr.nc')
