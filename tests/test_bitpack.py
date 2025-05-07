import numpy as np


def test_bitpack():
    from ti_plm.util import bitpack
    from ti_plm import PLM
    
    # test bitpacking function
    n = 100
    bitmaps = [np.ones((n, n), dtype=np.uint8) for _ in range(24)]  # generate 24 bitmaps full of 1
    
    plm = PLM.from_db('p67')
    
    # check bitstacking function on various class/instance objects
    for f in [bitpack, PLM.bitpack, plm.bitpack]:
        
        # check bitpacking 8 bitmaps
        stack = f(bitmaps[0:8])
        assert np.array_equal(stack.shape, np.array([1, n, n]))
        assert np.all(stack == 255)

        # check bitpacking 24 bitmaps
        stack = f(bitmaps)
        assert np.array_equal(stack.shape, np.array([3, n, n]))
        assert np.all(stack == 255)
