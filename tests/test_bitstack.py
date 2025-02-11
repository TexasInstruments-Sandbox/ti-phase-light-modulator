import numpy as np


def test_bitstack():
    from ti_phase_light_modulator.util import bitstack
    from ti_phase_light_modulator import PLM
    
    # test bitstacking function
    n = 100
    bitmaps = [np.ones((n, n), dtype=np.uint8) for _ in range(24)]  # generate 24 bitmaps full of 1
    
    plm = PLM.from_db('p67')
    
    # check bitstacking function on various class/instance objects
    for bs in [bitstack, PLM.bitstack, plm.bitstack]:
        
        # check bitstacking 8 bitmaps
        stack = bs(bitmaps[0:8])
        assert np.array_equal(stack.shape, np.array([1, n, n]))
        assert np.all(stack == 255)

        # check bitstacking 24 bitmaps
        stack = bs(bitmaps)
        assert np.array_equal(stack.shape, np.array([3, n, n]))
        assert np.all(stack == 255)
