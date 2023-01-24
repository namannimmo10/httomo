from typing import Dict
from inspect import signature

from numpy import ndarray
import cupy as cp

from httomolib import prep


def normalize(params: Dict, method_name: str, data: ndarray, flats: ndarray,
              darks: ndarray, gpu_id: int) -> ndarray:
    """Wrapper for httomolib.prep.normalize module.

    Parameters
    ----------
    params : Dict
        A dict containing all params of the wrapped httomolib function that are
        independent of HTTomo.
    method_name : str
        The name of the method to use in httomolib.prep.normalize.
    data : ndarray
        A numpy array containing the sample projections.
    flats :ndarray
        A numpy array containing the flatfield projections.
    darks : ndarray
        A numpy array containing the dark projections.
    gpu_id : int
        A GPU device index to execute operation on.

    Returns
    -------
    ndarray
        A numpy array of normalized projections.
    """
    cp._default_memory_pool.free_all_blocks()
    
    module = getattr(prep, 'normalize')
    # converting arrays to CuPy arrays
    data = getattr(module, method_name)(cp.asarray(data), cp.asarray(flats), cp.asarray(darks), gpu_id=gpu_id, **params)
    return cp.asnumpy(data)


def stripe(params: Dict, method_name: str, data: ndarray, gpu_id: int) -> ndarray:
    """Wrapper for httomolib.prep.stripe module.

    Parameters
    ----------
    params : Dict
        A dict containing all params of the wrapped httomolib function that are
        independent of httomo.
    method_name : str
        The name of the method to use in  httomolib.prep.phase.
    data : ndarray
        A numpy array of projections.
    gpu_id : int
        A GPU device index to execute operation on.        

    Returns
    -------
    ndarray
        A numpy array of projections with the stripes removed.
    """
    cp._default_memory_pool.free_all_blocks()

    module = getattr(prep, 'stripe')
    data = getattr(module, method_name)(cp.asarray(data), gpu_id=gpu_id, **params)
    return cp.asnumpy(data)



def phase(params: Dict, method_name: str, data: ndarray) -> ndarray:
    """Wrapper for httomolib.prep.phase module.

    Parameters
    ----------
    params : Dict
        A dict containing all params of the wrapped httomolib function that are
        independent of httomo.
    method_name : str
        The name of the method to use in  httomolib.prep.phase.
    data : ndarray
        A numpy array of projections.

    Returns
    -------
    ndarray
        A numpy array of projections with phase-contrast enhancement.
    """
    module = getattr(prep, 'phase')
    data = getattr(module, method_name)(data, **params)
    return data