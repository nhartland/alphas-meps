#!/usr/bin/python
import yoda
import math
import matplotlib.pyplot as plt

alphas_values = ["115","117", "118", "119", "121"]
experiments = 	["CMS_2011_S8950903"]
theory = "NLOPS-S-emission"
dPhi_cut = 2.8

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

def computeChi2(exp, alphas):
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
	aos = yoda.read(theory_path +theory+'/'+exp +'_0'+alphas+'_MC.yoda')
	for path in dataPaths:
		hs = [h for h in aos.values() if path in h.path]
		if len(hs) != 1:
			print "Error: Duplicate path!"
			quit();
		parseScatter2D(hs[0].mkScatter(), theoryPoints, theoryErrors)

	chi2=0
	for i in xrange(0,len(dataPoints)):
		chi2 += pow(dataPoints[i] - theoryPoints[i],2)/(pow(dataErrors[i],2) + pow(theoryErrors[i],2))
	return chi2/len(dataPoints)

####################################
print("Cut: DeltaPhi > " +str(dPhi_cut))
for exp in experiments:
	print("Analysing " + exp)
	chi2vals = []
	for a_s in alphas_values:
		chi2vals.append(computeChi2(exp, a_s))
		print(a_s + " : " + str(chi2vals[-1]))

	chi2fig, chi2ax = plt.subplots()
	chi2ax.set_ylabel("chi2")
	chi2ax.set_xlabel("alpha_S")
	chi2ax.xaxis.grid(True)
	chi2ax.yaxis.grid(True)
	chi2ax.plot(alphas_values, chi2vals, label = exp)
	chi2fig.savefig('chi2.pdf')
