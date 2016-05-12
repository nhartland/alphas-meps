#!/usr/bin/env python2

import heppyplotlib as hpl
import os
import yoda
import sys
sys.path.append('..')
import toolbox as tb

histos = hpl.rivet_paths('rawdata/Reweighting-0.yoda')
file_format = 'rawdata/Reweighting.MUR1_MUF1_PDF{}{:03d}-0.yoda'

for alphas in 0.115, 0.118, 0.121:
    lhapdfid = tb.alphas_to_lha(alphas)
    files = [file_format.format(lhapdfid, i) for i in range(0, 101)]
    combined = []
    for histo in histos:
        axes_list = None
        combined.append(hpl.combine(files, histo, hpl.standard_error))
    yoda.writeYODA(combined, 'CMS_2011_S8950903_{}_PDF.yoda'.format(alphas))
