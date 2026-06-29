import json
import os

# this script is used to analyse what different data is sent when you press different buttons on your RC. mostly experimental. 
# specifically, it scans for the different hexadecimals in the string of data. 



# --- Configuration ---

# specify path to file with your hex data. specifically, the same file you used to output hex data in ./bin_to_hex.py
outFile = './aircon-bits/hexData.json'

#---------------------------------------------------------------------------------------------------------------------------------------

settingToFind = input('please enter the name of the target difference to find (for example, for temperature enter \'temp\'): ')
valuesDone = []
settingHexPairList = []

with open(outFile, 'r') as f:
    fullData = json.load(f)


for key in fullData:
    config = fullData[key]
    misMatch = 'no'
    foundSetting = 'no'

    for setting in config:            # loop over each setting in config

        settingToFind_value = config[settingToFind]         # store the value of the setting 
        hexList = config['hexList']                         # store the hexList in that config

        if setting == settingToFind and settingToFind_value not in valuesDone:        # if the setting matches the one we want to find AND the value was not found already in prev. loops

            settingHexPairList.append([settingToFind_value, hexList])   # store the pair into a list

            valuesDone.append(settingToFind_value)              # append the value to a list that indicates this was found already, so further loops dont duplicate

            break
    

# print(f'settingHexPairList: {settingHexPairList}')

alreadyComparedIndexes = []
size = len(settingHexPairList)

for i in range(size):
    for j in range(i + 1, size):

        pair1 = settingHexPairList[i]
        pair2 = settingHexPairList[j]

        hexList1 = pair1[1]
        hexList2 = pair2[1]

        settingValue1 = pair1[0]
        settingValue2 = pair2[0]

        for k in range(len(pair1[1])):

            # check if each hex chunk in the two hex lists are the same. if not, print it out
            hex1 = pair1[1][k]
            hex2 = pair2[1][k]

            if hex1 != hex2 and k % 2 == 1:     #only show even indexes because odd indexes are bitwise inverses of the odd ones (0x00 is bitwise inverse of 0xff)
                print(f"found different hex at index {k}. for {settingToFind} = {settingValue1}, hex: {hex1} ; for {settingToFind} = {settingValue2}, hex: {hex2} ")





