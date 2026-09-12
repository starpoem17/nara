"""Process-wide defaults required before loading model libraries."""
import os


def configure_environment():
    """Set conservative local runtime defaults without overriding the caller."""
    os.environ.setdefault("VLLM_WORKER_MULTIPROC_METHOD", "spawn")
    os.environ.setdefault("OMP_NUM_THREADS", "4")
    os.environ.setdefault("OPENBLAS_NUM_THREADS", "4")
    os.environ.setdefault("MAX_JOBS", "2")
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
