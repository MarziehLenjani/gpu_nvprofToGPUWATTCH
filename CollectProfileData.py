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
    nIter=30


    parser = OptionParser(usage=usage)
    homeStr=os.environ['HOME']


    parser.add_option("-i", "--inputDir", type="string",
                      action="store", dest="inputDirectory", default= os.path.join(homeStr, "summaryResults/profileResult") ,
                      help="input directory ")
    parser.add_option("-o", "--outputDir", type="string",
                      action="store", dest="gpuwattch_xml_outputFiles", default= os.path.join(homeStr, "summaryResults/summaryofMetrics"),
                      help="output directory ")
    parser.add_option("-r", "--exe_run",
                      action="store_false", dest="readExeTimeFromRunResult", default=False,
                      help="readExeTimeFromRunResult")
    (opts, args) = parser.parse_args()

    readExeTimeFromRunResult = opts.readExeTimeFromRunResult

    (opts, args) = parser.parse_args()
    os.makedirs(opts.gpuwattch_xml_outputFiles, exist_ok=True)
    for operationName in os.listdir(opts.inputDirectory):
        subDirName=os.path.join(opts.inputDirectory, operationName)
        outputFileName=os.path.join(opts.gpuwattch_xml_outputFiles,operationName+".csv")
        print(operationName)
        summaryDataFrame = pd.DataFrame(columns=[metricNameStr, metricValueStr])
        for metricFileName in  os.listdir(subDirName):
            print(metricFileName)
            if metricFileName[0]!='.' and metricFileName[-3:-1]!='tmp':
                metricName=metricFileName[:-4]
                pathToMetricFileNames = os.path.join(opts.inputDirectory, operationName, metricFileName)
                print(pathToMetricFileNames+"\n")
                if (metricName!='powerConsumption'):
                    dataFrame = pd.read_csv(pathToMetricFileNames, comment='=')
                else:
                    tmpLines = open(pathToMetricFileNames, 'rt')
                    for line in tmpLines:
                        if "System profiling result" in line.strip():
                            break
                    open("pathToMetricFileNames" + "_tmp", 'wt').writelines(tmpLines)
                    dataFrame = pd.read_csv("pathToMetricFileNames" + "_tmp", comment='=')

                metricValue=0
                print(metricName)
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
                        if(readExeTimeFromRunResult==True):
                            infile = open(os.path.join(opts.inputDirectory, operationName,'executionTimeRunResult.csv', 'r'))
                            for line in infile:
                                metricValue=line *1.0e-3
                        else:

                            if(type(dataFrame.iloc[i].loc['Avg'])==str):

                                if((dataFrame.iloc[i].loc['Avg'][-1]!='s') and ('GPU activities' in dataFrame.iloc[i].loc['Type']) and ('CUDA memcpy' not in dataFrame.iloc[i].loc['Name']) ):
                                    metricValue +=float(dataFrame.iloc[i].loc['Avg'])* dataFrame.iloc[i].loc['Calls']
                                    print(dataFrame.iloc[i].loc['Avg']+"\n")
                    elif (metricName=='powerConsumption'):

                        tmpMax=0
                        for j in range(len(dataFrame)):
                            if ((j%4 ==3 ) and dataFrame.iloc[j].loc['Avg']>tmpMax):
                                tmpMax=dataFrame.iloc[j].loc['Avg']

                        metricValue=tmpMax

                    elif(type(dataFrame.iloc[i].loc['Avg']) != str):
                        metricValue +=(dataFrame.iloc[i].loc['Avg']) * dataFrame.iloc[i].loc['Invocations']
                if (metricName == 'executionTime'):
                    metricValue=metricValue/nIter


                if (percentage==True):
                    metricValue=metricValue/len(dataFrame)
                summaryDataFrame=summaryDataFrame.append({metricNameStr:metricName, metricValueStr:metricValue},ignore_index=True)

        print(summaryDataFrame)

        summaryDataFrame.to_csv(outputFileName)
            #if not dataFrame.empty:
                #print(dataFrame)


if __name__ == '__main__':
    main()
