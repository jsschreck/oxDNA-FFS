#!/usr/bin/env python
import sys

sys.path.append('~/CUDADNA/UTILS/')

import base
import order_parameters
import readers

def gen_complem_bonds_op(topologyfile,conffile,strandA=0,strandB=1):
	myreader = readers.LorenzoReader(conffile,topologyfile)
	mysystem = myreader.get_system()
	counter = 1
	print '{'
	print 'order_parameter = bond'
	print 'name = bonds'

	for i in range(len(mysystem._strands[strandA]._nucleotides )) :	
		if(mysystem._strands[strandB]._nucleotides[len(mysystem._strands[strandB]._nucleotides)-1-i]._btype + mysystem._strands[strandA]._nucleotides[i]._btype != 3):
			print "Error, base ",i, 'has no complemetary partner'
		l = len(mysystem._strands[strandB]._nucleotides)
		print 'pair'+str(counter) +' = ' + str(mysystem._strands[strandA]._nucleotides[i].index) + ',' + str((mysystem._strands[strandB]._nucleotides[l - 1 - i].index))
		counter += 1
	print '}'
	
def gen_complem_bonds_dist(topologyfile,conffile,strandA=0,strandB=1):
	myreader = readers.LorenzoReader(conffile,topologyfile)
	mysystem = myreader.get_system()
	counter = 1
	print '{'
	print 'order_parameter = mindistance'
	print 'name = dist'

	for i in range(len(mysystem._strands[strandA]._nucleotides )) :	
		if(mysystem._strands[strandB]._nucleotides[len(mysystem._strands[strandB]._nucleotides)-1-i]._btype + mysystem._strands[strandA]._nucleotides[i]._btype != 3):
			print "Error, base ",i, 'has no complemetary partner'
		l = len(mysystem._strands[strandB]._nucleotides)
		print 'pair'+str(counter) +' = ' + str(mysystem._strands[strandA]._nucleotides[i].index) + ',' + str((mysystem._strands[strandB]._nucleotides[l - 1 - i].index))
		counter += 1
	print '}'

def gen_any_bonds_op(topologyfile,conffile,strandA=0,strandB=1):
	myreader = readers.LorenzoReader(conffile,topologyfile)
	mysystem = myreader.get_system()
	counter = 1
	print '{'
	print 'order_parameter = bond'
	print 'name = all_bonds_'+str(strandA)+str(strandB)
	for i in mysystem._strands[strandA]._nucleotides :	
		for j in mysystem._strands[strandB]._nucleotides:
		   print 'pair'+str(counter) +' = ' + str(i.index) + ',' + str(j.index) 
		   counter += 1
	print '}'
	
def selfA(topologyfile,conffile,strandA):
	print '{'
	print 'order_parameter = bond'
	print 'name = self_bonds'+str(strandA)
	print 'pair1 = 1,18'
	print 'pair2 = 2,17'
	print 'pair3 = 3,16'
	print 'pair4 = 4,15'
	print '}'
	
def selfB(topologyfile,conffile,strandB):
	print '{'
	print 'order_parameter = bond'
	print 'name = self_bonds'+str(strandB)
	print 'pair1 = 31,48'
	print 'pair2 = 32,47'
	print 'pair3 = 33,46'
	print 'pair4 = 34,45'
	print '}'
	
def gen_any_bonds_strand(topologyfile,conffile,strandA):
	myreader = readers.LorenzoReader(conffile,topologyfile)
	mysystem = myreader.get_system()
	counter = 1
	print '{'
	print 'order_parameter = bond'
	print 'name = all_bonds_'+str(strandA)
	for i in mysystem._strands[strandA]._nucleotides :	
		for j in mysystem._strands[strandA]._nucleotides:
			if i != j:
		   		print 'pair'+str(counter) +' = ' + str(i.index) + ',' + str(j.index) 
		   		counter += 1
	print '}'




if len(sys.argv) < 3 :
	print 'Usage %s configuration topology [strandA=0  strandB=1]'
	sys.exit(1)	
conf = sys.argv[1]
top = sys.argv[2]
strA = 0
strB = 1
if(len(sys.argv) > 3):
	strA = int(sys.argv[3])
	strB = int(sys.argv[4])

gen_complem_bonds_op(top,conf,strA,strB)
selfA(top, conf, strA)
selfB(top, conf, strB)
gen_any_bonds_op(top,conf,strA,strB)
gen_any_bonds_strand(top, conf, strA)
gen_any_bonds_strand(top, conf, strB)
gen_complem_bonds_dist(top,conf,strA,strB)



