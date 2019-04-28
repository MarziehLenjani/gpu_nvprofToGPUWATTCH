
numCpu=4
#numCpu=8
#numCpu=16
numChannel=2
export MCPAT_HOME=/zf14/ml2au/McPAT_v1.0/mcpat
pyPathBase="/zf14/ml2au/gem5tomcpat/"
pyPath="${pyPathBase}run_mcpat.py"
configurationPrefix="RangMultipleC"
#gem5ResultBase="/bigtemp/ml2au/AxBenchResults/L1_1Cycle_4CPU/"
#gem5ResultBase="/bigtemp/ml2au/AxBenchResults/EnergyL2_5Cycle_4CPU2Ch/"
#gem5ResultBase="/bigtemp/ml2au/AxBenchResults/SensivityOverConversionLAtency/"
#gem5ResultBase="/bigtemp/ml2au/AxBenchResults/Sense4CPU/"
#gem5ResultBase="/bigtemp/ml2au/AxBenchResults/L2_5Cycle_8CPU/"
#gem5ResultBase="/bigtemp/ml2au/AxBenchResults/L2_5Cycle_16CPU/"
#gem5ResultBase="/bigtemp/ml2au/AxBenchResults/L2_5Cycle_16CPU_32MBL3/"
#gem5ResultBase="/bigtemp/ml2au/AxBenchResults/L2_5Cycle_8CPU_16MBL3/"
#gem5ResultBase="/bigtemp/ml2au/AxBenchResults/Prefetch16Cores/"
#gem5ResultBase="/bigtemp/ml2au/AxBenchResults/OutlierSensivity4Core/"
#gem5ResultBase="/zf14/ml2au/AxBenchResults/LocationSensivity4CoreRowNew/"
gem5ResultBase="/zf14/ml2au/AxBenchResults/CompressioninL3/"
templateBasePath="${pyPathBase}/templateFiles/"
#templateFile="${templateBasePath}template-xeon${numCpu}Core${numChannel}Ch.xml"
templateFile="${templateBasePath}template-xeon${numCpu}Core${numChannel}ChOverrhead.xml"
#vim $templateFile
outputBasrDir="/zf14/ml2au/AxBenchResults"
#OutPutPath=${outputBasrDir}/EnergyAndPerformanceSensivityOverLatency
#OutPutPath=${outputBasrDir}/Sens4Cpu
#OutPutPath=${outputBasrDir}/L2_5Cycle_8CPU
#OutPutPath=${outputBasrDir}/L2_5Cycle_16CPU
#OutPutPath=${outputBasrDir}/L2_5Cycle_16CPU_32MBL3
#OutPutPath=${outputBasrDir}/L2_5Cycle_8CPU_16MBL3
#OutPutPath=${outputBasrDir}/Prefetch16Cores
#OutPutPath=${outputBasrDir}/OutlierSensivity4Core
#OutPutPath=${outputBasrDir}/LocationSensivity4CoreNew
OutPutPath=${outputBasrDir}/CompressioninL3Summary
#OutPutPath=${outputBasrDir}/ComparisionAnalysis
templateBaseLineFile="${templateBasePath}template-xeon${numCpu}Core${numChannel}Ch.xml" 
BaselineConfigNumber="32"
#BaselineConfigNumber="10"
toDeleteilPath="/zf14/ml2au/gem5tomcpat/toDelete/"
toDeleteFile=${toDeleteilPath}mcpat-out.xml
mkdir -p $toDeleteilPath
[ -e $OutPutPath ] && rm -r -f $OutPutPath
mkdir -p $OutPutPath
#cd $gem5ResultBase
for AppDirectory in ${gem5ResultBase}*/ ; do
	AppName=${AppDirectory#"${gem5ResultBase}"}
	AppName=${AppName%"/"}
        echo "$AppName"
        outputFileName="${OutPutPath}/${AppName}.csv"
        echo "configNumber runtime Penergy Cenergy L2energy NoCenergy MCenergy" >> $outputFileName
	for ConfigDirectory in ${AppDirectory}*/; do 
		
		ConfigNUmber=${ConfigDirectory#"${AppDirectory}${configurationPrefix}"}
		ConfigNUmber=${ConfigNUmber%"/"}
		echo -n  "$ConfigNUmber  " >> $outputFileName
		[ -e ${toDeleteFile} ] &&  rm ${toDeleteFile} 
		if !( [ -s ${ConfigDirectory}stats.txt ] &&  [ -s ${ConfigDirectory}config.json ]) ; then
			echo "${ConfigDirectory}stats.txt is empty"
		
		else  
			if [ "$ConfigNUmber" == "$BaselineConfigNumber" ]; then
                                ${pyPathBase}GEM5ToMcPAT.py -q  ${ConfigDirectory}stats.txt ${ConfigDirectory}config.json ${templateBaseLineFile} -o  ${toDeleteFile}
                                ${pyPathBase}run_mcpat.py -q ${toDeleteFile}   ${ConfigDirectory}stats.txt  >> $outputFileName
			else
			
				${pyPathBase}GEM5ToMcPAT.py -q  ${ConfigDirectory}stats.txt ${ConfigDirectory}config.json ${templateFile} -o  ${toDeleteFile}
				${pyPathBase}run_mcpat.py -q ${toDeleteFile}   ${ConfigDirectory}stats.txt >> $outputFileName
			fi
		fi

	done 
done
	
