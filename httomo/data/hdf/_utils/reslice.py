from pathlib import Path

import numpy
from mpi4py.MPI import Comm

from httomo.data.hdf._utils import chunk, load
from httomo.utils import print_once


def reslice(
    data: numpy.ndarray,
    run_out_dir: Path,
    current_slice_dim: int,
    next_slice_dim: int,
    comm: Comm,
) -> tuple[numpy.ndarray, int]:
    """Reslice data by writing to hdf5 store with data chunked along a different
    dimension, and reading back along the new chunking dimension.

    Parameters
    ----------
    data : numpy.ndarray
        The data to be re-sliced.
    run_out_dir : Path
        The output directory to write the hdf5 file to.
    current_slice_dim : int
        The dimension along which the data is currently sliced.
    next_slice_dim : int
        The dimension along which the data should be sliced after re-chunking
        and saving.
    comm : Comm
        The MPI communicator to be used.

    Returns:
    tuple[numpy.ndarray, int]:
        A tuple containing the resliced data and the dimension along which it is
        now sliced.
    """
    print_once(f"<-------Reslicing/rechunking the data-------->", comm, colour="blue")

    # No need to reclice anything if there is only one process
    if comm.size == 1:
        print("Reslicing not necessary, as there is only one process")
        return data, next_slice_dim
    
    # Get shape of full/unsplit data, in order to set the chunk shape based on
    # the dims of the full data rather than of the split data
    data_shape = chunk.get_data_shape(data, current_slice_dim - 1)

    # build a list of what each process has to scatter to others, and make it
    # contiguous in memory (much faster to scatter, at the expense
    # of more CPU memory used for a copy)
    nprocs = comm.size
    length = data_shape[next_slice_dim - 1]
    split_indices = [round((length / nprocs) * r) for r in range(1, nprocs)]
    to_scatter = numpy.split(data, split_indices, axis=next_slice_dim-1)
    to_scatter = [numpy.ascontiguousarray(s) for s in to_scatter]

    # all-to-all MPI call distributes every processes list to every other process, 
    # and we concatenate them again across the resliced dimension
    new_data = numpy.concatenate(comm.alltoall(to_scatter), axis=current_slice_dim-1)
    
    return new_data, next_slice_dim