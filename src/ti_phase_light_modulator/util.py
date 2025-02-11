"""
Utility module containing objects shared by all other modules in this library.
"""
import numpy as np

TWO_PI = 2 * np.pi


class TIPLMException(Exception):
    pass


def bitstack(bitmaps: list|tuple):
    """Stack MSB of 8 bitmaps into 8-bit image
    
    Args:
        bitmaps (iterable): List of bitmaps to stack. Only the MSB in each bitmap will be used in the final stack. Each bitmap should be a uint8 array of the same shape.
    
    Raises:
        TIPLMException: Incorrect number of bitmaps provided
    
    Returns:
        ndarray: Uint8 array with the MSB from each of the provided bitmaps stacked along the 8 bits of the output.
    """
    if len(bitmaps) == 8:
        stacked = np.stack(bitmaps) & 1  # stack bitmaps and isolate MSB
        shifted = np.bitwise_left_shift(stacked, np.arange(8)[..., None, None])  # left shift each layer of the stack by 0-8 bits (using tensor broadcasting)
        return np.sum(shifted, axis=0)[None, ...]  # sum along stacked dimension and insert an extra dimension to the front so output is 3D (channel, row, column)
    elif len(bitmaps) == 24:
        rgb = []
        for n in range(3):
            stacked = np.stack(bitmaps[n:n+8]) & 1
            shifted = np.bitwise_left_shift(stacked, np.arange(8)[..., None, None])
            rgb.append(np.sum(shifted, axis=0))
        return np.stack(rgb)
    else:
        raise TIPLMException('Bitstack operation only support input bitmap list of length 8 or 24 corresponding to 1 or 3 channel output image, respectively.')
