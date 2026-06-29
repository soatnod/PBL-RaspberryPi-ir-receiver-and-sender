import json
import os
from accurate_receiver import increment_first_integer

# this script converts binary data into a hex list and stores it into a file. mostly experimental. 
# HOW TO USE: run the script as normal and follow the instructions. 
# example: 
# python3 bin_to_hex.py      <-- Enter
# please copy and paste your binary string here without quotes: 100000000000100000000000000000101111110111111111000000000011001111001100010010011011011011001000001101110011



# --- Configuration ---

# specify path to output file
outFile = './aircon-bits/hexData.json'

# make sure the status of your remote control matches the following values
temp = 27
tempChange = 'modekeypress'       # 'up', 'down', 'modekeypress'  did you press the temperature up button or down button, or cooler/heater button?
windSpeed = 2           # 0 to 5, 0 means auto
mode = 'cool'           # 'warm', 'dehumid', 'cool', 'fan'
directionToggle = 'no'  # 'yes', 'no'
timerOff = 0            # 0, 0.5, 1 to 9 in hours
timerOn = 0             # 0, 0.5, 1 to 12 in hours
stop = 'no'             # 'yes', 'no'

#---------------------------------------------------------------------------------------------------------------------------------------

ACstatus = [temp, tempChange, windSpeed, mode, directionToggle, timerOff, timerOn, stop]

def binToHex(binaryString):

    if len(binaryString) % 8 != 0:
        raise Exception("Length of input binary string must be a multiple of 8. ")


    hexList = []
    binaryList = list(binaryString)
    while len(binaryList) != 0:
        chunk = []
        for i in range(8):
            chunk.append(binaryList.pop(7 - i))    # start poping from the 8th digit in binaryList backwards until the first digit.

        chunkString = ''.join(chunk)
        chunkInt = int(chunkString, 2)
        chunkHex = hex(chunkInt)

        hexList.append(chunkHex)

    print(hexList)
    return hexList

def hexDataDict(hexList, ACstatus):

    data = {
        'temp': ACstatus[0], 
        'tempChange': ACstatus[1],
        'windSpeed': ACstatus[2], 
        'mode': ACstatus[3], 
        'directionToggle': ACstatus[4], 
        'timerOff': ACstatus[5], 
        'timerOn': ACstatus[6], 
        'stop': ACstatus[7], 
        'hexList': hexList
    }

    return data

def writeDataToFile(file, dict):
    numberOfSettings = len(dict) - 1

    fileIsEmpty = 'no'
    fullData = {}

    found = 'no'
    configKey = ''
    lastKeyInConfig = ''
    if os.stat(file).st_size == 0:             #check if file is empty.
        fileIsEmpty = 'yes'
        pass
    else:
        with open(file, 'r') as f:
            fullData = json.load(f)

        for key in fullData:
            config = fullData[key]
            misMatch = 'no'
            
            if  found == 'yes':
                break

            for i in range(0, numberOfSettings):            # loop over each setting in config
                if list(config.values())[i] == list(dict.values())[i]:  # check if current settings match the ones found in config
                    pass
                else:
                    misMatch = 'yes'
                    break

            if misMatch == 'no':
                configKey = key
                lastKeyInConfig = list(config.keys())[len(config) - 1]

                found = 'yes'
    
    if found == 'yes':
        fullData[configKey]['hexList'] = dict['hexList']
        print(f"modifying config key: {configKey}, replacing old hexList with new hexList value.")
    else:
        if fileIsEmpty == 'yes':
            newConfigKey = "config_1"
        else:
            configKeysList = list(fullData.keys())
            lastConfigkey = configKeysList[len(configKeysList) - 1]
            newConfigKey = increment_first_integer(lastConfigkey)
        fullData[newConfigKey] = dict

    with open(file, 'w') as f:
        json.dump(fullData, f, indent=4)


if __name__ == '__main__':
    
    binaryString = input("please copy and paste your binary string here without quotes: ")

    hexList = binToHex(binaryString)

    data = hexDataDict(hexList, ACstatus)

    writeDataToFile(outFile, data)