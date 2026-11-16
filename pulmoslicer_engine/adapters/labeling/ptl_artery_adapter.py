"""LB03: pulmonary-artery-specific PTL entry point."""

from .ptl_inference import predict_ptl


def predict(mask, runtime, **kwargs):
    return predict_ptl(mask, "artery", runtime, **kwargs)
