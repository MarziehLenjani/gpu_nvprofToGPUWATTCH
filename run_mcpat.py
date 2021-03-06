#!/usr/bin/python
import sys
import re
import os
import json
import types
import math

import subprocess as subp
from optparse import OptionParser
mcpat_home = os.getenv( "MCPAT_HOME", "/if22/ml2au/McPAT_v1.0/mcpat")
mcpat_bin = "mcpat"

class parse_node:
    def __init__(this,key=None,value=None,indent=0):
        this.key = key
        this.value = value
        this.indent = indent
        this.leaves = []
    
    def append(this,n):
        #print 'adding parse_node: ' + str(n) + ' to ' + this.__str__() 
        this.leaves.append(n)

    def get_tree(this,indent):
        padding = ' '*indent*2
        me = padding + this.__str__()
        kids = map(lambda x: x.get_tree(indent+1), this.leaves)
        return me + '\n' + ''.join(kids)
        
    def getValue(this,key_list):
        #print 'key_list: ' + str(key_list)
        #if (this.key == key_list[0]):
	if ((this.key == key_list[0]) or  ((key_list[0] in this.key) and (":" in this.key) and ( ("cores" in this.key) or ("Memory Controllers" in this.key)))):
            #print 'success'
            if len(key_list) == 1:
                return this.value
            else:
                kids = map(lambda x: x.getValue(key_list[1:]), this.leaves)
                #print 'kids: ' + str(kids) 
                return ''.join(kids)
        return ''        
        
    def __str__(this):
        return 'k: ' + str(this.key) + ' v: ' + str(this.value)

class parser:

    def dprint(this,astr):
        if this.debug:
            print (this.name,
            print astr

    def __init__(this, data_in):
        this.debug = False
        this.name = 'mcpat:mcpat_parse'

        buf = StringIO.StringIO(data_in)
      
        this.root = parse_node('root',None,-1)
        trunk = [this.root]

        for line in buf:
            
            #this.dprint('l: ' + str(line.strip()))

            indent = len(line) - len(line.lstrip())
            equal = '=' in line
            colon = ':' in line
            useless = not equal and not colon
            items = map(lambda x: x.strip(), line.split('='))

            branch = trunk[-1]

            if useless: 
                #this.dprint('useless')
                pass 

            elif equal:
                assert(len(items) > 1)

                n = parse_node(key=items[0],value=items[1],indent=indent)
                branch.append(n)

                this.dprint('new parse_node: ' + str(n) )

            else:
                
                while ( indent <= branch.indent):
                    this.dprint('poping branch: i: '+str(indent) +\
                                    ' r: '+ str(branch.indent))
                    trunk.pop()
                    branch = trunk[-1]
                
                this.dprint('adding new leaf to ' + str(branch))
                n = parse_node(key=items[0],value=None,indent=indent)
                branch.append(n)
                trunk.append(n)
                
        
    def get_tree(this):
        return this.root.get_tree(0)

    def getValue(this,key_list):
        value = this.root.getValue(['root']+key_list) 
        assert(value != '')
        return value

#runs McPAT and gives you the total energy in mJs
def main():
    global opts
    homeStr = os.environ['HOME']
    usage = "--help"
    parser = OptionParser(usage=usage)
    parser.add_option("-q", "--quiet", 
        action="store_false", dest="verbose", default=True,
        help="don't print status messages to stdout")

    parser.add_option("-o", "--outs", type="string",
                      action="store", dest="gpuwattch_xml_outputFiles", default=os.path.join(homeStr, "summaryResults/gpuwattch_xml_outputFiles"),
                      help="output file ")
    (opts, args) = parser.parse_args()

    #print getTimefromStats(args[1])
    #print runMcPAT(args[0])
    runtime,Penergy,Cenergy,L2energy,NoCenergy,MCenergy = getEnergy(args[0], args[1])
    #print "energy is %f mJ" % energy
    print ("%f %f %f %f %f %f" , runtime,Penergy,Cenergy,L2energy, NoCenergy, MCenergy)
    #readConfigFile(args[1])
    #readMcpatFile(args[2])
    #dumpMcpatOut(opts.out)

def getEnergy(procConfigFile, statsFile):
    #leakage, dynamic = runMcPAT(procConfigFile)
    Pleakage,Pdynamic,Cleakage,Cdynamic,L3leakage,L3dynamic,NoCleakage,NoCdynamic,MCleakage,MCdynamic=runMcPAT(procConfigFile)
    runtime = getTimefromStats(statsFile)
    Penergy = (Pleakage + Pdynamic)*runtime
    Cenergy = (Cleakage + Cdynamic)*runtime
    L2energy = (L3leakage + L3dynamic)*runtime
    NoCenergy = (NoCleakage + NoCdynamic)*runtime
    MCenergy = (MCleakage + MCdynamic)*runtime
    #print "leakage: %f, dynamic: %f and runtime: %f" % (leakage, dynamic, runtime)
    return runtime,Penergy,Cenergy,L2energy,NoCenergy,MCenergy

def runMcPAT(procConfigFile):
    command = mcpat_home
    command += "/%s" % mcpat_bin
    command += " -print_level 0"
    command += " -infile %s" % procConfigFile
    #print command
    output = subp.check_output(command, shell=True)
    p = parser(output)
    #print p.get_tree()
    Pleakage = p.getValue(['Processor:', 'Total Leakage'])
    Pdynamic = p.getValue(['Processor:', 'Runtime Dynamic'])
    Pleakage = re.sub(' W','', Pleakage) 
    Pdynamic = re.sub(' W','', Pdynamic)
#---------------------------------------
    Cleakage = p.getValue(['Processor:',"Total Cores", 'Subthreshold Leakage'])
    Cdynamic = p.getValue(['Processor:', "Total Cores",'Runtime Dynamic'])
    Cleakage = re.sub(' W','', Cleakage)
    Cdynamic = re.sub(' W','', Cdynamic)
#-------------------------------------------
    L3leakage = p.getValue(['Processor:',"Total L3s:", 'Subthreshold Leakage'])
    L3dynamic = p.getValue(['Processor:', "Total L3s:",'Runtime Dynamic'])
    L3leakage = re.sub(' W','', L3leakage)
    L3dynamic = re.sub(' W','', L3dynamic)
#----------------------------------------
    NoCleakage = p.getValue(['Processor:',"Total NoCs (Network/Bus):", 'Subthreshold Leakage'])
    NoCdynamic = p.getValue(['Processor:', "Total NoCs (Network/Bus):",'Runtime Dynamic'])
    NoCleakage = re.sub(' W','', NoCleakage)
    NoCdynamic = re.sub(' W','', NoCdynamic)
#----------------------------------------
    MCleakage = p.getValue(['Processor:',"Total MCs", 'Subthreshold Leakage'])
    MCdynamic = p.getValue(['Processor:', "Total MCs",'Runtime Dynamic'])
    MCleakage = re.sub(' W','', MCleakage)
    MCdynamic = re.sub(' W','', MCdynamic)
    return (float(Pleakage), float(Pdynamic), float(Cleakage), float(Cdynamic),float(L3leakage), float(L3dynamic),float(NoCleakage), float(NoCdynamic),float(MCleakage), float(MCdynamic))
    

def getTimefromStats(statsFile):
    if opts.verbose: print "Reading simulation time from: %s" %  statsFile
    F = open(statsFile)
    ignores = re.compile(r'^---|^$')
    statLine = re.compile(r'([a-zA-Z0-9_\.:-]+)\s+([-+]?[0-9]+\.[0-9]+|[0-9]+|nan)')
    retVal = None
    for line in F:
        #ignore empty lines and lines starting with "---"  
        if not ignores.match(line):
            statKind = statLine.match(line).group(1)
            statValue = statLine.match(line).group(2)
            if statKind == 'sim_seconds':
		#print  "sim_seconds is found"
		#print "it is %s" % statValue
                retVal = float(statValue)
		#print "%f" %retVal
		F.close()
		return retVal


if __name__ == '__main__':
    main()
