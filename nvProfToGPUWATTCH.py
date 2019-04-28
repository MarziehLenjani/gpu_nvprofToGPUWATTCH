#!/usr/bin/python
from optparse import OptionParser
from inspect import currentframe, getframeinfo


import sys
import re
import json
import types
import math
#import elementpath
from xml.etree import ElementTree as ET
#from xml.etree import ElementTree as ET
import pandas as pd
import os

import io
import subprocess as subp
#from xml.etree.ElementTree import XMLTreeBuilder

# This is a wrapper over xml parser so that
# comments are preserved.
# source: http://effbot.org/zone/element-pi.htm

def parse(source):
    #return ET.parse(source, PIParser())
    return ET.parse(source)


def main():

    global opts
    usage = "usage: --help"
    parser = OptionParser(usage=usage)
    homeStr = os.environ['HOME']
    cf = currentframe()


    parser.add_option("-q", "--quiet",
                      action="store_false", dest="verbose", default=True,
                      help="don't print status messages to stdout")
    parser.add_option("-p", "--pass", type="string",
                      action="store", dest="password",
                      default="ABCD",
                      help="password ")
    parser.add_option("-g", "--genParam",
                      action="store_false", dest="GenerateEmptyParameters", default=False,
                      help="generate the name of parameters")
    parser.add_option("-x", "--xmlOuts", type="string",
                      action="store", dest="gpuwattch_xml_outputFiles", default=os.path.join(homeStr, "summaryResults/gpuwattch_xml_outputFiles"),
                      help="xml output files ")
    parser.add_option("-o", "--energy_outs", type="string",
                      action="store", dest="energy_outputFiles", default=os.path.join(homeStr, "summaryResults/energy_outputFiles"),
                      help="enery output file ")
    parser.add_option("-c", "--csvParam", type="string",
                      action="store", dest="csvOut", default="temp_parammetrName.csv",
                      help="name of the file containing the name of the parameters ")
    parser.add_option("-t", "--template", type="string",
                      action="store", dest="templateFileName", default="templateFiles/gpuwattch_P100.xml",
                      help="output file ")
    parser.add_option("-s", "--stats", type="string",
                      action="store", dest="staDirectory", default=os.path.join(homeStr, "summaryResults/summaryofMetrics"),
                      help="input file ")
    parser.add_option("-r", "--run", type="string",
                      action="store", dest="runResultFileName", default="summaryResults/runResult.csv",
                      help="name of the file containing the  run result")
    parser.add_option("-e", "--expr", type="string",
                      action="store", dest="expressionFileName", default="profileMetricsToParamExpressions.csv",
                      help="name of the file containing the  expressions that determines relation between metrics and params")
    parser.add_option("-b", "--binary", type="string",
                      action="store", dest="gpuwatBinFile", default="gpuwattch.out",
                      help="name of the binary file")
    (opts, args) = parser.parse_args()
    gpuwattch_xml_outputFilesPath=os.path.join(homeStr,opts.gpuwattch_xml_outputFiles)
    statDirectoryPath=os.path.join(homeStr,opts.staDirectory)
    runResultFileName=os.path.join(homeStr,opts.runResultFileName)
    expressionFileName=opts.expressionFileName
    os.makedirs(gpuwattch_xml_outputFilesPath, exist_ok=True)
    energy_outputFilesPath=os.path.join(homeStr,opts.energy_outputFiles)
    os.makedirs(energy_outputFilesPath,exist_ok=True)

    #global parameterNames
    getRunTimeFromRunResultFile=False
    global parameColumnName
    global valueColumName
    global metricNameStr
    global metricValueStr
    global executionTimeColumnName
    global operationColumnName
    global frequencyOfGPU
    global expressionColName
    parameColumnName = "paramName"
    valueColumName= "paramValue"
    metricNameStr='metricName'
    metricValueStr='metricValue'
    executionTimeColumnName='TimeVar'
    operationColumnName = 'operation'
    expressionColName='expressionCol'
    frequencyOfGPU=1328

    templateMcpat=readMcpatFile(opts.templateFileName)
    if(opts.GenerateEmptyParameters ):
        dumpCSVOut(templateMcpat,opts.csvOut)
    dataFramContaingExpressions = pd.read_csv(expressionFileName,dtype={'ID': object})
    print(dataFramContaingExpressions)
    generateGPUwattch_outputFiles(dataFramContaingExpressions, templateMcpat, getRunTimeFromRunResultFile,runResultFileName, statDirectoryPath, gpuwattch_xml_outputFilesPath)
    #os.system('sshpass -p'+ opts.password+' scp -r ~/summaryResults/gpuwattch_xml_outputFiles  ml2au@power1.cs.virginia.edu:summaryResults/')
    getEnergy(energy_outputFilesPath,gpuwattch_xml_outputFilesPath,statDirectoryPath)



#################################
def generateGPUwattch_outputFiles(dataFramContaingExpressions,templateMcpat,getRunTimeFromRunResultFile, runResultFileName, statDirectoryPath, gpuwattch_xml_outputFilesPath):

    if(getRunTimeFromRunResultFile):
        dataFrameContainingRunResult=pd.read_csv(runResultFileName)
        print(dataFrameContainingRunResult)
    for operationFileName in  os.listdir(statDirectoryPath):
        if operationFileName[0]!='.':
            operationName=operationFileName[:-4]
            print(operationName)
            pathTooperationStatFileNames=os.path.join(statDirectoryPath,operationFileName)
            dataFrameContainingStats=pd.read_csv(pathTooperationStatFileNames)

            if (getRunTimeFromRunResultFile):
                oprerationDf = dataFrameContainingRunResult.loc[
                    dataFrameContainingRunResult[operationColumnName] == operationName]
                if oprerationDf.empty:
                    print(operationName + "not found in csv file containg run time values \n")
            else:
                oprerationDf=0

            dataFrameContainingParams=mapStatsToParams(dataFramContaingExpressions,dataFrameContainingStats,oprerationDf,operationName)
            print(dataFrameContainingParams)
            dumpMcpatOut(templateMcpat, dataFrameContainingParams, operationName, gpuwattch_xml_outputFilesPath)



###################################

##################################
def dumpCSVOut(templateMcpat,outFile):
    rootElem = templateMcpat.getroot()
    #configMatch = re.compile(r'config\.([a-zA-Z0-9_:\.]+)')
    # replace params with values from the GEM5 config file
    i = 0
    parameterNames= pd.DataFrame(columns=[parameColumnName,valueColumName])
    for param in rootElem.iter('stat'):
        name = param.attrib['name']
        value = param.attrib['value']
        # print("name is ",name)
        # print("value is ", value)

        if '_match_mcpat' in value:
            allConfs = parameterNames.loc[parameterNames[parameColumnName]==value]

            if(allConfs.empty ):
                parameterNames=parameterNames.append({parameColumnName:value, valueColumName:0},ignore_index=True)
                i=i+1
                print (str(i)+":"+value+"\n")
    if opts.verbose: print("Writing to the empty CSV file: %s" % outFile)
    print(parameterNames)
    parameterNames.to_csv(outFile)
def dumpMcpatOut(templateMcpat, dataFrameContainingParams, operationName, gpuwattch_xml_outputFilesPath):
    rootElem = templateMcpat.getroot()
    #configMatch = re.compile(r'config\.([a-zA-Z0-9_:\.]+)')
    # replace params with values from the GEM5 config file
    i = 0
    for param in rootElem.iter('stat'):
        name = param.attrib['name']
        value = param.attrib['value']
        # print("name is ",name)
        # print("value is ", value)

        if '_match_mcpat' in value:
            allConfs = dataFrameContainingParams.loc[dataFrameContainingParams[parameColumnName]==value]

            if(not allConfs.empty ):
                i=i+1
                #print (str(i)+":"+str(len(allConfs))+"\n")
                #print (allConfs.iloc[0].loc[parameColumnName])
                valueNumber = allConfs.iloc[0].loc[valueColumName]
                #print (str(value)+"*************************")
                param.attrib['value'] = str(eval(str(valueNumber)))
                #print(value + " found:"+str(eval(str(valueNumber)))+"\n")
            else:
                print ( value +" not found\n" )
                param.attrib['value']=str(0)

    xmlOutputFileName=os.path.join(gpuwattch_xml_outputFilesPath,operationName+".xml")
    if opts.verbose: print("Writing input to McPAT in: %s" % xmlOutputFileName)
    templateMcpat.write(xmlOutputFileName)


def readMcpatFile(templateFile):
    #global templateMcpat
    if opts.verbose: print("Reading McPAT template from: %s" % templateFile)
    templateMcpat = parse(templateFile)
    return templateMcpat


# print dir(templateMcpat)


def readConfigFile(configFile):
    global config
    if opts.verbose: print("Reading config from: %s" % configFile)
    F = open(configFile)
    config = json.load(F)
    # print config
    # print config["system"]["membus"]
    # print config["system"]["cpu"][0]["clock"]
    F.close()

def mapStatsToParams(dataFramContaingExpressions,dataFrameContaingStats,oprerationDf,operationName):


    #dataFrameContaingParams = pd.read_csv("temp_parammetrName.csv") # to test rest of the code
    dataFrameContaingParams=pd.DataFrame(columns=[parameColumnName, valueColumName])
    regulareExpression = re.compile(r'([a-zA-Z0-9_:]+)')
    listOfNotFound = []

    for j in range(len(dataFramContaingExpressions)):
        tempMetricName = dataFramContaingExpressions.iloc[j].loc[parameColumnName]
        expression = dataFramContaingExpressions.iloc[j].loc[expressionColName]
        tempValue = 0
        """
        if(tempMetricName=='total_cycles_match_mcpat' or tempMetricName=='idle_cycles_match_mcpat' or tempMetricName=='busy_cycles_match_mcpat' ):
            print("*************************\n")
            #exectime = oprerationDf.iloc[0].loc[executionTimeColumnName] #ldToDelete
            exectime=
            #any parameter that you can pass as a fixed parameter can be put in the expression file
            clock_rateDf=dataFramContaingExpressions.loc[dataFramContaingExpressions[parameColumnName]=='clock_rate']
            if not clock_rateDf.empty:
                clock_rate=clock_rateDf.iloc[0].loc[expressionColName]
                if(tempMetricName=='total_cycles_match_mcpat' or tempMetricName == 'busy_cycles_match_mcpat'):

                    tempValue=(exectime/1.0e3)/(1.0/(eval(clock_rate)/1.0e6))  #excutionTime is in milisecond and clock rate in MHZ
                if (tempMetricName == 'idle_cycles_match_mcpat'):
                    tempValue =0


            else:
                sys.exit("clock rate is not found \n")
        else:
        """
        allStats = regulareExpression.findall(expression)
        expr = expression
        tempValue=0
        print(expr+"  len is:"+str(len(allStats)))

        for i in range(len(allStats)):
            if(allStats[i]=='clock_rate'):

                clock_rateDf = dataFramContaingExpressions.loc[
                    dataFramContaingExpressions[parameColumnName] == 'clock_rate']
                if not clock_rateDf.empty:
                    clock_rate = clock_rateDf.iloc[0].loc[expressionColName]
                    valueOfStat=eval(clock_rate)
                    expr = re.sub('%s' % allStats[i], str(valueOfStat), expr)
            else:
                tempDf=dataFrameContaingStats.loc[dataFrameContaingStats[metricNameStr]==allStats[i]]
                print(tempDf)
                if not tempDf.empty:
                    valueOfStat=tempDf.iloc[0].loc[metricValueStr]
                    expr = re.sub('%s' % allStats[i], str(valueOfStat), expr)
                    print (expr+":"+str(valueOfStat))
                else:

                    listOfNotFound.append(allStats[i])

        tempValue=str(eval(expr))
        dataFrameContaingParams=dataFrameContaingParams.append({parameColumnName: tempMetricName, valueColumName: tempValue}, ignore_index=True)
    print(dataFrameContaingStats)
    print("***WARNING: the following does not exist in stats***")
    print(*listOfNotFound)
    return dataFrameContaingParams
def getStat(dataFrameContaingStats,statName):
    tempDf = dataFrameContaingStats.loc[dataFrameContaingStats[metricNameStr] == statName]

    #print(tempDf)
    if not tempDf.empty:
        valueOfStat = tempDf.iloc[0].loc[metricValueStr]
    else:
        print(statName + " not found \n")
    return valueOfStat
##########################################
mcpat_home = os.getenv("MCPAT_HOME", "/if22/ml2au/McPAT_v1.0/mcpat")
mcpat_bin = "mcpat"


class parse_node:
    def __init__(this, key=None, value=None, indent=0):
        this.key = key
        this.value = value
        this.indent = indent
        this.leaves = []

    def append(this, n):
        # print 'adding parse_node: ' + str(n) + ' to ' + this.__str__()
        this.leaves.append(n)

    def get_tree(this, indent):
        padding = ' ' * indent * 2
        me = padding + this.__str__()
        kids = map(lambda x: x.get_tree(indent + 1), this.leaves)
        return me + '\n' + ''.join(kids)

    def getValue(this, key_list):
        # print 'key_list: ' + str(key_list)
        # if (this.key == key_list[0]):
        if ((this.key == key_list[0]) or ((key_list[0] in this.key) and (":" in this.key) and (
                ("cores" in this.key) or ("Memory Controllers" in this.key)))):
            # print 'success'
            if len(key_list) == 1:
                return this.value
            else:
                kids = map(lambda x: x.getValue(key_list[1:]), this.leaves)
                # print 'kids: ' + str(kids)
                return ''.join(kids)
        return ''

    def __str__(this):
        return 'k: ' + str(this.key) + ' v: ' + str(this.value)


class parser:

    def dprint(this, astr):
        if this.debug:
            print (this.name+ ",")
            print (astr)

    def __init__(this, data_in):
        this.debug = False
        this.name = 'gpuWattch:gpuWattch_parse'

        buf = io.StringIO(data_in)

        this.root = parse_node('root', None, -1)
        trunk = [this.root]

        for line in buf:

            # this.dprint('l: ' + str(line.strip()))

            indent = len(line) - len(line.lstrip())
            equal = '=' in line
            colon = ':' in line
            useless = not equal and not colon
            items = map(lambda x: x.strip(), line.split('='))

            branch = trunk[-1]

            if useless:
                # this.dprint('useless')
                pass

            elif equal:
                assert (len(items) > 1)

                n = parse_node(key=items[0], value=items[1], indent=indent)
                branch.append(n)

                this.dprint('new parse_node: ' + str(n))

            else:

                while (indent <= branch.indent):
                    this.dprint('poping branch: i: ' + str(indent) + \
                                ' r: ' + str(branch.indent))
                    trunk.pop()
                    branch = trunk[-1]

                this.dprint('adding new leaf to ' + str(branch))
                n = parse_node(key=items[0], value=None, indent=indent)
                branch.append(n)
                trunk.append(n)

    def get_tree(this):
        return this.root.get_tree(0)

    def getValue(this, key_list):
        value = this.root.getValue(['root'] + key_list)
        assert (value != '')
        return value


# runs McPAT and gives you the total energy in mJs
def getEnergy(energyFiles, gpuwattch_xml_outputFiles, statDirectoryPath):
    EnergyDf = pd.DataFrame()
    for operationFileName in os.listdir(statDirectoryPath):
        if operationFileName[0] != '.':
            operationName = operationFileName[:-4]
            print(operationName)
            pathTooperationStatFileNames = os.path.join(statDirectoryPath, operationFileName)
            dataFrameContainingStats = pd.read_csv(pathTooperationStatFileNames)
            xmlFile=os.path.join(gpuwattch_xml_outputFiles, operationFileName)
            EnergyDf = runAndGetEnergy(xmlFile, dataFrameContainingStats,operationName)
    print (EnergyDf)
def runAndGetEnergy(xmlFile,dataFrameContainingStats,operationName):
    operationNameStr='operation'
    runtimeStr = 'runtimeStr'
    PenergyStr = 'PenergyStr'
    CenergyStr = 'CenergyStr'
    L3energyStr = 'L3energyStr'
    NoCenergyStr = 'NoCenergyStr'
    MCenergyStr = 'MCenergyStr'
    tmpEnergyDf = pd.DataFrame(columns=[runtimeStr,PenergyStr,CenergyStr,L3energyStr,NoCenergyStr,MCenergyStr])

    #leakage, dynamic = runMcPAT(procConfigFile)
    #Pleakage, Pdynamic, Cleakage, Cdynamic, L3leakage, L3dynamic, NoCleakage, NoCdynamic, MCleakage, MCdynamic=0,0,0,0,0,0,0,0,0,0
    Pleakage,Pdynamic,Cleakage,Cdynamic,L3leakage,L3dynamic,NoCleakage,NoCdynamic,MCleakage,MCdynamic=runGPUWATTCH(xmlFile)
    runtime = getStat(dataFrameContainingStats,"executionTime")
    Penergy = (Pleakage + Pdynamic)*runtime
    Cenergy = (Cleakage + Cdynamic)*runtime
    L3energy = (L3leakage + L3dynamic)*runtime
    NoCenergy = (NoCleakage + NoCdynamic)*runtime
    MCenergy = (MCleakage + MCdynamic)*runtime
    temmpDic={operationNameStr:operationName,runtimeStr:runtime, PenergyStr:Penergy, CenergyStr:Cenergy, L3energyStr:L3energy, NoCenergyStr:NoCenergy, MCenergyStr:MCenergy}
    tmpEnergyDf=tmpEnergyDf.append(temmpDic,ignore_index=True)
    #print "leakage: %f, dynamic: %f and runtime: %f" % (leakage, dynamic, runtime)
    return tmpEnergyDf


def runGPUWATTCH(procConfigFile):
    command = opts.gpuwatBinFile
    command += " -print_level 0"
    command += " -infile %s" % procConfigFile
    # print command
    output = subp.check_output(command, shell=True)
    p = parser(output)
    # print p.get_tree()
    Pleakage = p.getValue(['Processor:', 'Total Leakage'])
    Pdynamic = p.getValue(['Processor:', 'Runtime Dynamic'])
    Pleakage = re.sub(' W', '', Pleakage)
    Pdynamic = re.sub(' W', '', Pdynamic)
    # ---------------------------------------
    Cleakage = p.getValue(['Processor:', "Total Cores", 'Subthreshold Leakage'])
    Cdynamic = p.getValue(['Processor:', "Total Cores", 'Runtime Dynamic'])
    Cleakage = re.sub(' W', '', Cleakage)
    Cdynamic = re.sub(' W', '', Cdynamic)
    # -------------------------------------------
    L3leakage = p.getValue(['Processor:', "Total L3s:", 'Subthreshold Leakage'])
    L3dynamic = p.getValue(['Processor:', "Total L3s:", 'Runtime Dynamic'])
    L3leakage = re.sub(' W', '', L3leakage)
    L3dynamic = re.sub(' W', '', L3dynamic)
    # ----------------------------------------
    NoCleakage = p.getValue(['Processor:', "Total NoCs (Network/Bus):", 'Subthreshold Leakage'])
    NoCdynamic = p.getValue(['Processor:', "Total NoCs (Network/Bus):", 'Runtime Dynamic'])
    NoCleakage = re.sub(' W', '', NoCleakage)
    NoCdynamic = re.sub(' W', '', NoCdynamic)
    # ----------------------------------------
    MCleakage = p.getValue(['Processor:', "Total MCs", 'Subthreshold Leakage'])
    MCdynamic = p.getValue(['Processor:', "Total MCs", 'Runtime Dynamic'])
    MCleakage = re.sub(' W', '', MCleakage)
    MCdynamic = re.sub(' W', '', MCdynamic)
    return (float(Pleakage), float(Pdynamic), float(Cleakage), float(Cdynamic), float(L3leakage), float(L3dynamic),
            float(NoCleakage), float(NoCdynamic), float(MCleakage), float(MCdynamic))


if __name__ == '__main__':
    main()
