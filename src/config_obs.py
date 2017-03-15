import math
import numpy as np
import yoda
import sys
from itertools import islice
from config import *



#### configuring exp-file ####

d_tags = ["157", "54", "62", "70", "78", "86"] #observable tags for ln(y3), T, HJM, B_T, B_W, C

obs = list(d_obs)
for p in range(0, len(theorypath), 1):
	for files in filelist:

		outputyoda_raw = open(theorypath[p] + files + '_obs_raw.yoda', 'w')
		for n in d_tags:
			with open(theorypath[p] + files + '.yoda') as f:
				for line in f:
					if "BEGIN YODA_HISTO1D /ALEPH_2004_S5765862/d{}-x01-y01".format(n) in line:
						outputyoda_raw.write(line)
						line = f.next()
						while line != "\n":
							outputyoda_raw.write(line)
							line = f.next()
						outputyoda_raw.write("\n")

	f.close()
	outputyoda_raw.close()

	### configuring exp-files
	for exp, x in map(None, experiments, obs):
		output_raw = open(datapath + exp + "_obs_raw.yoda", 'w')
		for n in d_tags:
			with open(datapath + exp + ".yoda") as f:
				for line in f:
					#print line
					if "BEGIN YODA_SCATTER2D /REF/ALEPH_2004_S5765862/d{}-x01-y01".format(n) in line:
						output_raw.write(line)
						line= f.next()
						while line != "\n":
							output_raw.write(line)
							line = f.next()
						output_raw.write("\n")

		f.close()
		output_raw.close()

		observable_line = []
		#i = 1
	
		d = list(x)
		output = open(datapath + exp + "_obs.yoda", 'w')

		for n in d_tags:
			i = 1
			with open(datapath + exp + "_obs_raw.yoda") as f:
				for line in f:
					if "BEGIN YODA_SCATTER2D /REF/ALEPH_2004_S5765862/d{}-x01-y01".format(n) in line:
						observable_line.append(i)
					i += 1
		#print observable_line

		for count in range(0, len(d), 1):
			j = 1
			if d[count] ==1:
				with open(datapath + exp + "_obs_raw.yoda") as f:
					for line in islice(f, observable_line[count] -1, None):
						output.write(line)
						if line == '\n':
							break
						j += 1

		f.close()
		output.close()	#configuring of exp-file completed.

	##### configuring mcdata-files #####	
		for files in filelist:
			outputyoda = open(theorypath[p] + exp + files + '_obs.yoda', "w")
			observable_line = []
			d = list(x)
	
			for n in d_tags:
				i = 1
				with open(theorypath[p] + files + '_obs_raw.yoda') as f:
					for line in f:
						if "BEGIN YODA_HISTO1D /ALEPH_2004_S5765862/d{}-x01-y01".format(n) in line:
							observable_line.append(i)
						i += 1

			print observable_line

			for count in range(0, len(d), 1):
				j = 1
				if d[count] == 1:
					with open(theorypath[p] + files + '_obs_raw.yoda') as f:
						for line in islice(f, observable_line[count] -1, None):
							outputyoda.write(line)
							if line == '\n':
								break
							j += 1

			f.close()
			outputyoda.close()


#############################################################

#dataPaths = []
#aos = yoda.read(datapath + exp + '_obs.yoda')
#for aopath, ao in aos.iteritems():
#	dataPaths.append(ao.path[4:])
#print 'dataPath:', dataPaths

#for path in dataPaths:
#	hs = [h for h in aos.values() if path in h.path]
#	#print hs, hs[0].points	

#dPoints = []
#dError = []
##print "Points!", hs[0].mkScatter().points
#for bin in hs[0].mkScatter().points:
#	#print bin.x, bin.y
#	if 0.75 < bin.x < 0.9:
#		dPoints.append(bin.y)
#		dError.append((bin.yErrs.plus + bin.yErrs.minus)/2.0)

##print "d", dPoints
			


	
	
	



