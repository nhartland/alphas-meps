#!/usr/bin/python
import yoda
import math
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator, FormatStrFormatter, FixedLocator, FuncFormatter
import sys
import numpy as np
from matplotlib.pyplot import *
#from sympy.solvers import solve
from sympy import Symbol, solve

from config import *

import matplotlib as mpl
mpl.use('pgf')


########################################
def figsize(scale):
    fig_width_pt = 443.863                       
    inches_per_pt = 1.0/72.27                       # Convert pt to inch
    golden_mean = (np.sqrt(5.0)-0.75)/2.0           # Aesthetic ratio
    fig_width = fig_width_pt*inches_per_pt*scale    # width in inches
    fig_height = fig_width*golden_mean              # height in inches
    fig_size = [fig_width,fig_height]
    return fig_size

pgf_with_latex = {
    "pgf.texsystem": "pdflatex",
    "text.usetex": True,
    "font.family": "serif",
    "font.serif": [],                   # blank entries should cause plots to inherit fonts from the document
    "font.sans-serif": [],
    "font.monospace": [],
    "axes.labelsize": 16,               
    "text.fontsize": 12,                 
    "legend.fontsize": 14,               
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "figure.figsize": figsize(1.0), 
    "pgf.preamble": [
        r"\usepackage[utf8]{inputenc}",    
        r"\usepackage[T1]{fontenc}",        # plots will be generated using this preamble
        #r"\usepackage{pgfplots}"
        #r"\usepgfplotslibrary{external}",
        #r"\tikzexternalize",
        ]
}
mpl.rcParams.update(pgf_with_latex)

mpl.rcParams['xtick.major.size'] = 4
mpl.rcParams['xtick.major.width'] = 1.25
mpl.rcParams['xtick.minor.size'] = 2
mpl.rcParams['xtick.minor.width'] = 1.25
mpl.rcParams['ytick.major.size'] = 4
mpl.rcParams['ytick.major.width'] = 1.25
mpl.rcParams['ytick.minor.size'] = 2
mpl.rcParams['ytick.minor.width'] = 1.25

majorLocatorx = MultipleLocator(2)
minorLocatorx = MultipleLocator(1)


####################################

def parseScatter2D(ao, dPoints, dErrors, fitrange):
	if type(ao) != yoda.Scatter2D:
		print "Error: Datafile AnalysisObject is not a Scatter2D"
		quit();
	for n in range(0, len(fitrange), 1):
		if d_obs[0][n] == 1:
			for bin in ao.points:
				if fitrange[n][0] < bin.x < fitrange[n][1]:
					dPoints.append(bin.y)
					dErrors.append((bin.yErrs.plus + bin.yErrs.minus)/2.0)
	#print 'dPoints', dPoints

####################################
def computeChi2(theoryp, exp, alphas, fitrange):
	# Read experimental data and systematics
	dataPaths  = []
	dataPoints = []
	dataErrors = []
	aos = yoda.read(datapath + exp +'_obs.yoda')
	for aopath, ao in aos.iteritems():
		dataPaths.append(ao.path[4:])
		parseScatter2D(ao, dataPoints, dataErrors, fitrange)
        #print 'paths', dataPaths, len(dataPaths)

	theoryPoints = []
	theoryErrors = []
	aos = yoda.read(theoryp + '/' + exp +'Reweighting.MUR1_MUF1_PDF252'+alphas+'-4_obs.yoda') #reading yoda-files
	for path in dataPaths:
		hs = [h for h in aos.values() if path in h.path]
                #print 'h', hs, len(hs)
                if len(hs) != 1:
	            print "Error: Duplicate path!"
	            quit();
	        parseScatter2D(hs[0].mkScatter(), theoryPoints, theoryErrors, fitrange)

	chi2=0
	for i in xrange(0,len(dataPoints)):
		chi2 += pow(dataPoints[i] - theoryPoints[i],2)/(pow(dataErrors[i],2) + pow(theoryErrors[i],2))
	return chi2/len(dataPoints)

####################################
def fit(theoryp, th, exp, fitrange): 
	i=0
	for name in name_obs:
		if d_obs[0][i] == 1:
			f = open(th + "/fit" + '_' + exp + '_' + name + ".dat", 'w')
			sys.stdout = f
			print("Analysing " + exp)
			chi2vals = []

			for a_s in pdf_tag:
				chi2vals.append(computeChi2(theoryp, exp, a_s, fitrange))
				print ("PDF252" + a_s + ": " + str(chi2vals[-1]))

			z = np.polyfit(alphas_values, chi2vals, 3) #performing polynomial fit: ax^3 + bx^2 + cx + d.
			fit = np.poly1d(z)
			x_val = np.linspace(alphas_values[0], alphas_values[-1], 100) #values for plot
			y_val = fit(x_val)                                            #values for plot
	
			#finding minimum of chi2-fit
			crit = fit.deriv().r
			r_crit = crit[crit.imag==0].real
			test = fit.deriv(2)(r_crit) #2nd derivative > 0 for minimum?
			alphas_min = r_crit[test>0] #values for plot
			chi2_min = fit(alphas_min) #values for plot

			#finding error of alphas_min using chi2_min + 1 = f(alphas) -> two values for alphas: upper and bottom limit
			roots = (fit - 1 - chi2_min).r
			roots_list = roots[roots.imag==0].real
			rl = list(roots_list) #necessary for using the remove method. Since there are 3 roots, one has to delete the "unphysical" one.

			if any([d_obs[0][0] == 1 and th == "LEP/MEPSNLO_hadro", d_obs[0][0] == 1 and th == "LEP/MEPSNLO", d_obs[0][4] == 1 and th == "LEP/MEPSNLO"]):
				rl.remove(max(rl))
			else:
				rl.remove(min(rl))

			print 'list', rl	
			alphas_up = max(rl) - alphas_min[0] #error alphas up
			alphas_down = alphas_min[0] - min(rl) #error alphas down
			
		i += 1

	return chi2vals, x_val, y_val, alphas_min, chi2_min, alphas_up, alphas_down

##########################################

#plotting

mepsnlo = fit(theorypath[0], theory[0], experiments[0], fit_region_new)
mepsnlo_hadro = fit(theorypath[1], theory[1], experiments[0], fit_region_new)

j = 0
for name, a in map(None, name_obs, ref_alphas):
	if d_obs[0][j] == 1:
		chi2fig, chi2ax = plt.subplots()
		#chi2ax.set_title("%s" %(name))
		chi2ax.set_ylabel("$\\chi^2$")
		chi2ax.set_xlabel("$\\alpha_\mathrm{s}$")
		chi2ax.xaxis.grid(True)
		chi2ax.yaxis.grid(True)
		chi2ax.plot(alphas_values, mepsnlo[0], "+", color="cornflowerblue") #plotting the chi2 data-points
		chi2ax.plot(alphas_values, mepsnlo_hadro[0], "+", color="tomato")
		#chi2ax.plot(meps_hadro_ref[1], meps_hadro_ref[2], color='cornflowerblue', label='$\\chi^2$-Fit: MEPS@LO, fitrange: ref')
		#chi2ax.plot(meps_hadro_new[1], meps_hadro_new[2], color='tomato', label='$\\chi^2$-Fit: MEPS@LO, fitrange: new')
		#chi2ax.plot(meps_hadro_ref[3], meps_hadro_ref[4], "o", color='cornflowerblue', label='$\\alpha_\mathrm{s}$ ref: %s (+ %s - %s)' %(round(meps_hadro_ref[3][0], 2),round(meps_hadro_ref[5],2),round(meps_hadro_ref[6],2)))
		#chi2ax.plot(meps_hadro_new[3], meps_hadro_new[4], "o", color='tomato', label='$\\alpha_\mathrm{s}$ new: %s (+ %s - %s)' %(round(meps_hadro_new[3][0], 2),round(meps_hadro_new[5],2),round(meps_hadro_new[6],2)))
		chi2ax.plot(mepsnlo[1], mepsnlo[2], color='cornflowerblue', label='$\\chi^2$-Fit: MEPS@NLO, Hadro: Off') #plotting the polynomial fit function
		chi2ax.plot(mepsnlo_hadro[1], mepsnlo_hadro[2], color='tomato', label='$\\chi^2$-Fit: MEPS@NLO, Hadro: On')
		chi2ax.plot(mepsnlo[3], mepsnlo[4], "o", color='cornflowerblue', label='$\\alpha_\mathrm{s}$ non-Hadro: %s (+ %s - %s)' %(round(mepsnlo[3][0], 2),round(mepsnlo[5],2),round(mepsnlo[6],2))) #plotting a_s-min with error in label
		chi2ax.plot(mepsnlo_hadro[3], mepsnlo_hadro[4], "o", color='tomato', label='$\\alpha_\mathrm{s}$ Hadro: %s (+ %s - %s)' %(round(mepsnlo_hadro[3][0], 2),round(mepsnlo_hadro[5],2),round(mepsnlo_hadro[6],2)))	
		#chi2ax.axvline(x=a, color='red', linestyle='--', label='alphas_ref')
		plt.xlim((108,128))
		chi2ax.xaxis.set_major_locator(majorLocatorx)
		chi2ax.xaxis.set_minor_locator(minorLocatorx)
		chi2ax.legend(loc='upper left', numpoints=1) #upper right for MEPS and upper left for MEPSNLO 
		for axis in ['top', 'bottom', 'left', 'right']:
			chi2ax.spines[axis].set_linewidth(1.25)
		chi2fig.tight_layout()
		chi2fig.savefig('fig/MEPSNLO_' + name + '.pdf')
	j += 1


