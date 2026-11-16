"""LB04: pulmonary-vein-specific PTL entry point."""

from .ptl_inference import predict_ptl


def predict(mask, runtime, **kwargs):
    return predict_ptl(mask, "vein", runtime, **kwargs)
