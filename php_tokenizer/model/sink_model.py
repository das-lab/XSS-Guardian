#!/usr/bin/env python3
from joblib import load


def load_sink_model():
    model_path = __file__.replace('sink_model.py',
                                  'sink_cluster_kmeans.model')
    return load(model_path)


__all__ = ['load_sink_model']
