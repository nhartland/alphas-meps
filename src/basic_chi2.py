#!/usr/bin/python
import yoda
import math

experiments = 	["CMS_2011_S8950903"]
theory = "NLOPS-S-emission"
dPhi_cut = 2.3

####################################

data_path = "../data/"
theory_path = "../mc-data/"

####################################

def parseScatter2D(ao, dPoints, dErrors):
    if type(ao) != yoda.Scatter2D:
        print "Error: Datafile AnalysisObject is not a Scatter2D"
        quit();
    for bin in ao.points:
    	if bin.x > dPhi_cut:
	    	dPoints.append(bin.y)
	    	dErrors.append((bin.yErrs.plus + bin.yErrs.minus)/2.0)

####################################

for exp in experiments:
	print("Analysing " + exp)

	# Read experimental data and systematics
	dataPaths  = []
	dataPoints = []
	dataErrors = []
	aos = yoda.read(data_path + exp +'_TOTAL.yoda')
	for aopath, ao in aos.iteritems():
		dataPaths.append(ao.path[4:])
		parseScatter2D(ao, dataPoints, dataErrors)

	theoryPoints = []
	theoryErrors = []
	aos = yoda.read(theory_path +theory+'/'+exp +'_0115_MC.yoda')
	for path in dataPaths:
		hs = [h for h in aos.values() if path in h.path]
		if len(hs) != 1:
			print "Error: Duplicate path!"
			quit();
		parseScatter2D(hs[0].mkScatter(), theoryPoints, theoryErrors)

	chi2=0
	for i in xrange(0,len(dataPoints)):
		chi2 += pow(dataPoints[i] - theoryPoints[i],2)/(pow(dataErrors[i],2) + pow(theoryErrors[i],2))
	print(chi2/len(dataPoints))
                #         # Add cutflow
                #         cutflow = []
                #         for bin in ao.bins:
                #                 cutflow.append(bin.sumW)
                #         cutflows[folder+regime] = cutflow