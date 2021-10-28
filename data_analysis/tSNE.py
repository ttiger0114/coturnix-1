import numpy as np
from sklearn.manifold import TSNE

def tsne_and_save_result(parmas, latents):
    learning_rate, n_iter, n_iter_without_progress = params
    model = TSNE(learning_rate=100, n_iter=1500, n_iter_without_progress=100)
    transformed = model.fit_transform(latents)

    np.save("/content/drive/MyDrive/캡스톤디자인프로젝트/tsne_result_{}_{}_{}.npy".format(learning_rate, n_iter, n_iter_without_progress), transformed)