#!/usr/bin/python
import math

# Conversion of LHAPDF ID to alpha_S value
def lha_to_alphas(lhaid):
	pdfsets={
		264000 : 0.115,
		265000 : 0.117,
		266000 : 0.119,
		267000 : 0.121,
		260000 : 0.118 
	}

	baseset = 1000*math.floor(lhaid/1000.0)
	return pdfsets[baseset]