# -*- coding: utf8 -*-

import numpy as np
from pyxmeans import XMeans as xmeans


dataset = 'genes-cancer'
# dataset = 'RiMG75'

embedding_file = 'data/{}/subj_obj_embeddings.txt'.format(dataset)
data = np.loadtxt(embedding_file)
print data.shape
x_means = xmeans(2)
x_means.fit(data)
