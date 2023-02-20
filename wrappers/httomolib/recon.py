from typing import Dict
from inspect import signature

import numpy as np
import cupy as cp
from cupy import ndarray

from httomo.utils import print_once

from mpi4py.MPI import Comm

from httomo.utils import pattern, Pattern
from httomolib import recon


@pattern(Pattern.sinogram)
def algorithm(params: Dict,
              method_name: str, 
              data: np.ndarray,
              angles_radians: np.ndarray,
              gpu_id: int) -> np.ndarray:
    """Wrapper for httomolib.recon.algorithm module.

    Parameters
    ----------
    params : Dict
        A dict containing all params of the wrapped httomolib function that are
        independent of httomo.
    method_name : str
        The name of the method to use in  httomolib.recon.algorithm.
    data : ndarray
        A numpy array of projections.
    angles_radians : ndarray
        A numpy array of angles in radians.
    gpu_id : int
        A GPU device index to execute operation on.        

    Returns
    -------
    ndarray
        A CuPy array of projections with stripes removed.
    """
    module = getattr(recon, 'algorithm')

    cp._default_memory_pool.free_all_blocks()
    cp.cuda.Device(gpu_id).use()    
    
    # TODO: possibly change this clumsy way of operating with numpy/cupy arrays depending on the methods choice
    if method_name == "reconstruct_tomobar":
        # as now this function does not require ncore parameter 
        # TODO: not elegant, needs rethinking
        try:
            del params["ncore"]
        except:
            pass
        if params["algorithm"] == "FBP3D_device":            
            data = getattr(module, method_name)(cp.asarray(data), angles=angles_radians, gpu_id=gpu_id, **params)
            return cp.asnumpy(data)            
        else:
            data = getattr(module, method_name)(data, angles=angles_radians, gpu_id=gpu_id, **params)
            return data
        
    if method_name == "reconstruct_tomopy":
        data = getattr(module, method_name)(data, angles=angles_radians, gpu_id=gpu_id, **params)
        return data   


@pattern(Pattern.sinogram)
def rotation(params: Dict, method_name:str, comm: Comm, data: np.ndarray, gpu_id: int) -> float:
    """Wrapper for the httomolib.recon.rotation module.

    Parameters
    ----------
    params : Dict
        A dict containing all params of the wrapped tomopy function that are
        independent of HTTomo.
    method_name : str
        The name of the method to use in tomopy.recon.rotation.
    comm : Comm
        The MPI communicator to be used.
    data : ndarray
        A CuPy array of projections.

    Returns
    -------
    float
        The center of rotation.
    """
    module = getattr(recon, 'rotation')

    # as now this function does not require ncore parameter 
    # TODO: not elegant, needs rethinking
    try:
        del params["ncore"]
    except:
        pass
    
    cp._default_memory_pool.free_all_blocks()
    cp.cuda.Device(gpu_id).use()        
   

    method_func = getattr(module, method_name)
    rot_center = 0
    mid_rank = int(round(comm.size / 2) + 0.1)
    if comm.rank == mid_rank:
        if params['ind'] == 'mid':
            params['ind'] = data.shape[1] // 2 # get the middle slice
        rot_center = method_func(cp.asarray(data), **params)
    rot_center = comm.bcast(rot_center, root=mid_rank)
    print_once("The center of rotation is {}".format(rot_center), comm, colour="cyan")

    return cp.asnumpy(rot_center)