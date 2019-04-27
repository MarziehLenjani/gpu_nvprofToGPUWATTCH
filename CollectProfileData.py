#!/usr/bin/python
from optparse import OptionParser
import sys
import re
import json
import types
import math
import os

import pandas as pd



def main():

    global opts
    usage= "--help"
    metricNameStr='metricName'
    metricValueStr='metricValue'

    parser = OptionParser(usage=usage)
    homeStr=os.environ['HOME']


    parser.add_option("-i", "--inputDir", type="string",
                      action="store", dest="inputDirectory", default= os.path.join(homeStr, "summaryResults/profileResult") ,
                      help="input directory ")
    parser.add_option("-o", "--outputDir", type="string",
                      action="store", dest="gpuwattch_xml_outputFiles", default= os.path.join(homeStr, "summaryResults/summaryofMetrics"),
                      help="output directory ")

    (opts, args) = parser.parse_args()
    os.makedirs(opts.gpuwattch_xml_outputFiles, exist_ok=True)
    for operationName in os.listdir(opts.inputDirectory):
        subDirName=os.path.join(opts.inputDirectory, operationName)
        outputFileName=os.path.join(opts.gpuwattch_xml_outputFiles,operationName+".csv")
        print(operationName)
        summaryDataFrame = pd.DataFrame(columns=[metricNameStr, metricValueStr])
        for metricFileName in  os.listdir(subDirName):
            if metricFileName[0]!='.':
                metricName=metricFileName[:-4]
                pathToMetricFileNames = os.path.join(opts.inputDirectory, operationName, metricFileName)
                dataFrame = pd.read_csv(pathToMetricFileNames, comment='=')


                metricValue=0
                for i in range(len(dataFrame)):
                    print(type(dataFrame.iloc[i].loc['Avg']))
                    percentage=False
                    if((type(dataFrame.iloc[i].loc['Avg']) == str) and (dataFrame.iloc[i].loc['Avg'][-1]=='%')):
                        percentage=True
                        print ("***************"+dataFrame.iloc[i].loc['Avg'][-1])
                        tmpStr=dataFrame.iloc[i].loc['Avg'][:-1]
                        #print()
                        dataFrame['Avg']=dataFrame['Avg'].str.rstrip('%').astype('float') / 100.0 #TODO weighted value for  percentage  values for multiple kernels

                        metricValue+=dataFrame.iloc[i].loc['Avg']
                    elif (metricName == 'executionTime'):
                        if(type(dataFrame.iloc[i].loc['Avg'])==str):

                            if((dataFrame.iloc[i].loc['Avg'][-1]!='s') and ('GPU activities' in dataFrame.iloc[i].loc['Type']) and ('CUDA memcpy' in dataFrame.iloc[i].loc['Name']) ):
                                metricValue +=float(dataFrame.iloc[i].loc['Avg'])
                    elif(type(dataFrame.iloc[i].loc['Avg']) != str):
                        metricValue +=dataFrame.iloc[i].loc['Avg']

                if (percentage==True):
                    metricValue=metricValue/len(dataFrame)
                summaryDataFrame=summaryDataFrame.append({metricNameStr:metricName, metricValueStr:metricValue},ignore_index=True)

        print(summaryDataFrame)

        summaryDataFrame.to_csv(outputFileName)
            #if not dataFrame.empty:
                #print(dataFrame)


if __name__ == '__main__':
    main()
