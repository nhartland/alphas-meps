#!/usr/bin/python
import math

# Conversion of LHAPDF ID to alpha_S value
def lha_to_alphas(lhaid):
	pdfsets={
		264 : 0.115,
		265 : 0.117,
		266 : 0.119,
		267 : 0.121,
		260 : 0.118 
	}

	baseset = int(math.floor(lhaid/1000.0))
	return pdfsets[baseset]