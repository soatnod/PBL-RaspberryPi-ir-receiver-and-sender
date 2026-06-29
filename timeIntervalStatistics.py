import sys
import math

# this script is intended to read a file with bare bone time data and output the standard deviation 
# and average of the list of data. 

# --- Configuration ---

# specify path to barebone time data file
fileName = './time-intervals/bareboneTimeData.txt'



#---------------------------------------------------------------------------------------------------------------------------------------

dataList = []

with open(fileName, "r", encoding='UTF-8') as f:
    for line in f: #read the file one line at a time
        lineInt = int(line.rstrip()) #convert string number into integer number
        dataList.append(lineInt)

print(dataList)

def getAverageFromList(list):
    sum = 0
    for i in list:
        sum += i
    average = sum / len(list)
    return average

def getStandardDeviation(list):
    
    average = getAverageFromList(list)
    population_size = len(list)
    sum_of_square_difference = 0

    for i in list:
        sum_of_square_difference += (i - average)**2
    
    standard_deviation = math.sqrt(sum_of_square_difference / population_size)

    return standard_deviation


standard_deviation = round(getStandardDeviation(dataList), 2)
number_of_data = len(dataList)
average = getAverageFromList(dataList)
print(f"standard deviation: {standard_deviation}, number of data: {number_of_data}, average: {average}")