#general settings

datapath = "../data/" # here we find for example the ALEPH-data yoda-files. 
theorypath = ["../mc-data/LEP/MEPSNLO/", "../mc-data/LEP/MEPSNLO_hadro/"] #yoda-files for MEPSNLO and MEPSNLO+hadro. 
theory = ["LEP/MEPSNLO", "LEP/MEPSNLO_hadro"] #in these directories the chi2-values are stored in a dat-file. Make sure that these directories exist in the first place.  

pdf_tag = ["71", "72", "73","74", "75", "76", "77", "78", "79", "80", "81", "82", "70", "83", "84", "85", "86", "87", "88", "89", "90"]
alphas_values= [108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128]
filelist = ["Reweighting.MUR1_MUF1_PDF252{}-4".format(tag) for tag in pdf_tag] 

experiments = ["ALEPH_2004_S5765862"]

name_obs = ["ln(y3)", "T", "HJM", "BT", "BW", "C"]
d_obs = [[1, 0, 0, 0, 0, 0]] #observable tags for the different experiments. 1 -> we consider this observable for fit. Order of the observables as in name_obs
fit_region_ref = [[1.6, 4.0], [0.75, 0.91], [0.10, 0.22], [0.16, 0.30], [0.09, 0.19], [0.36, 0.74]] #reference fit regions from the NNLO-paper for the six observables
fit_region_new = [[1.2, 4.0], [0.65, 0.93], [0.09, 0.23], [0.12, 0.34], [0.06, 0.20], [0.30, 0.74]] #chosen fit range. Can be varied. 

ref_alphas = ["118.6", "126.5", "121.1", "126.8", "119.6", "125.2"] #NNLO-paper fit results
