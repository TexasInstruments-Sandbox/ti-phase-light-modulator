import numpy as np
from pytest import raises


def test_p47():
    from ti_phase_light_modulator import PLM
    
    # create test phase map of phase values associated with each displacement level of a p47 SHV device
    phase = np.array([[0.0, 0.0126, 0.0259, 0.0495, 0.0710, 0.0878, 0.1382, 0.2153, 0.3274, 0.3610, 0.4204, 0.5046, 0.5916, 0.6730, 0.8254, 1.0]]) * 15/16 * 2 * np.pi
    
    # define expect phase state index corresponding to each phase value above
    phase_idx_expected = np.array([[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]])

    # define expected memory values for each displacement level
    memory_expected = np.array([[3, 2, 1, 7, 0, 6, 5, 4, 11, 10, 9, 8, 15, 14, 13, 12]])
    
    # define expected bits we should get for the given phase map, which accounts for memory mapping and bit layout on electrodes under PLM mirrors
    bits_expected = np.array([
    #   Phase state index
    #    0       1       2       3       4       5       6       7       8       9       10      11      12      13      14      15
    #   Memory value
    #    3       2       1       7       0       6       5       4       11      10      9       8       15      14      13      12
    #   Electrode cell values
        [0, 0,   0, 0,   0, 0,   1, 0,   0, 0,   1, 0,   1, 0,   1, 0,   0, 1,   0, 1,   0, 1,   0, 1,   1, 1,   1, 1,   1, 1,   1, 1],
        [1, 1,   0, 1,   1, 0,   1, 1,   0, 0,   0, 1,   1, 0,   0, 0,   1, 1,   0, 1,   1, 0,   0, 0,   1, 1,   0, 1,   1, 0,   0, 0]
    ], dtype=np.uint8)
    
    plm = PLM.from_db('p47')
    
    # test individual functions related to calculating bits from phase map
    phase_idx = plm.quantize(phase)
    assert np.array_equal(phase_idx, phase_idx_expected)
    memory = plm.memory_lut[phase_idx]
    assert np.array_equal(memory, memory_expected)
    bits = plm.bitpack(phase_idx)
    assert np.array_equal(bits, bits_expected)
    
    # test full algorithm
    out = plm.process_phase_map(phase, replicate_bits=False, enforce_shape=False)
    assert np.array_equal(out, bits_expected)
    
    # test phase wrapping (2pi --> 0)
    assert np.array_equal(
        plm.process_phase_map(np.array([[[2 * np.pi]]]), replicate_bits=False, enforce_shape=False),
        np.array([[  # note this is a flipped 0 index phase state
            [0, 0],
            [1, 1]
        ]])
    )

    # make sure shape enforcement is working
    # calling process_phase_map without enforce_shape=False will throw an exception if the input phase map shape doesn't match plm.shape
    from ti_phase_light_modulator import TIPLMException
    with raises(TIPLMException):
        plm.process_phase_map(phase)
    

def test_p67():
    from ti_phase_light_modulator import PLM
    
    # create test phase map of phase values associated with each displacement level of a p67 SHV device
    phase = np.array([[0.0, 0.0126, 0.0259, 0.0495, 0.0710, 0.0878, 0.1382, 0.2153, 0.3274, 0.3610, 0.4204, 0.5046, 0.5916, 0.6730, 0.8254, 1.0]]) * 15/16 * 2 * np.pi

    # define expect phase state index corresponding to each phase value above
    phase_idx_expected = np.array([[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]])
    
    # define expected memory values for each displacement level
    memory_expected = np.array([[3, 2, 1, 7, 0, 6, 5, 4, 11, 10, 9, 8, 15, 14, 13, 12]])
    
    # define expected bits we should get for the given phase map, which accounts for memory mapping and bit layout on electrodes under PLM mirrors
    bits_expected_unflipped = np.array([
    #   Phase state index
    #    0       1       2       3       4       5       6       7       8       9       10      11      12      13      14      15
    #   Memory value
    #    3       2       1       7       0       6       5       4       11      10      9       8       15      14      13      12
    #   Electrode cell values
        [1, 0,   1, 0,   0, 0,   1, 0,   0, 0,   1, 0,   0, 0,   0, 0,   1, 1,   1, 1,   0, 1,   0, 1,   1, 1,   1, 1,   0, 1,   0, 1],
        [1, 0,   0, 0,   1, 0,   1, 1,   0, 0,   0, 1,   1, 1,   0, 1,   1, 0,   0, 0,   1, 0,   0, 0,   1, 1,   0, 1,   1, 1,   0, 1]
    ], dtype=np.uint8)
    bits_expected = np.flip(bits_expected_unflipped, -1)  # flip along column axis (horizontal) for p67 plm

    plm = PLM.from_db('p67')
    
    # test individual functions related to calculating bits from phase map
    phase_idx = plm.quantize(phase)
    assert np.array_equal(phase_idx, phase_idx_expected)
    memory = plm.memory_lut[phase_idx]
    assert np.array_equal(memory, memory_expected)
    bits = plm.bitpack(phase_idx)
    assert np.array_equal(bits, bits_expected)
    
    # test full algorithm
    out = plm.process_phase_map(phase, replicate_bits=False, enforce_shape=False)
    assert np.array_equal(out, bits_expected)
    
    # test phase wrapping (2pi --> 0)
    assert np.array_equal(
        plm.process_phase_map(np.array([[[2 * np.pi]]]), replicate_bits=False, enforce_shape=False),
        np.array([[  # note this is a flipped 0 index phase state
            [0, 1],
            [0, 1]
        ]])
    )

    # make sure shape enforcement is working
    # calling process_phase_map without enforce_shape=False will throw an exception if the input phase map shape doesn't match plm.shape
    from ti_phase_light_modulator import TIPLMException
    with raises(TIPLMException):
        plm.process_phase_map(phase)


def test_p67_minus_pi_to_pi():
    from ti_phase_light_modulator import PLM
    
    # create test phase map of phase values associated with each displacement level of a p67 SHV device
    # make this phase array 3D to test algorithm handling of >2D phase data
    phase = np.array([[[0.0, 0.0126, 0.0259, 0.0495, 0.0710, 0.0878, 0.1382, 0.2153, 0.3274, 0.3610, 0.4204, 0.5046, 0.5916, 0.6730, 0.8254, 1.0]]]) * 15/16 * 2 * np.pi - np.pi

    # define expect phase state index corresponding to each phase value above
    phase_idx_expected = np.array([[[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]]])
    
    # define expected memory values for each displacement level
    memory_expected = np.array([[[3, 2, 1, 7, 0, 6, 5, 4, 11, 10, 9, 8, 15, 14, 13, 12]]])
    
    # define expected bits we should get for the given phase map, which accounts for memory mapping and bit layout on electrodes under PLM mirrors
    bits_expected_unflipped = np.array([[
    #   Phase state index
    #    0       1       2       3       4       5       6       7       8       9       10      11      12      13      14      15
    #   Memory value
    #    3       2       1       7       0       6       5       4       11      10      9       8       15      14      13      12
    #   Electrode cell values
        [1, 0,   1, 0,   0, 0,   1, 0,   0, 0,   1, 0,   0, 0,   0, 0,   1, 1,   1, 1,   0, 1,   0, 1,   1, 1,   1, 1,   0, 1,   0, 1],
        [1, 0,   0, 0,   1, 0,   1, 1,   0, 0,   0, 1,   1, 1,   0, 1,   1, 0,   0, 0,   1, 0,   0, 0,   1, 1,   0, 1,   1, 1,   0, 1]
    ]], dtype=np.uint8)
    bits_expected = np.flip(bits_expected_unflipped, -1)  # flip along column axis (horizontal) for p67 plm

    plm = PLM.from_db('p67', phase_range=(-np.pi, np.pi))
    
    # test individual functions related to calculating bits from phase map
    phase_idx = plm.quantize(phase)
    assert np.array_equal(phase_idx, phase_idx_expected)
    memory = plm.memory_lut[phase_idx]
    assert np.array_equal(memory, memory_expected)
    bits = plm.bitpack(phase_idx)
    assert np.array_equal(bits, bits_expected)
    
    # test full algorithm
    out = plm.process_phase_map(phase, replicate_bits=False, enforce_shape=False)
    assert np.array_equal(out, bits_expected)


def test_p67_3d():
    from ti_phase_light_modulator import PLM
    
    # create test phase map of phase values associated with each displacement level of a p67 SHV device
    # make this phase array 3D to test algorithm handling of >2D phase data
    phase = np.array([[
        [0.0, 0.0126, 0.0259, 0.0495], 
        [0.0710, 0.0878, 0.1382, 0.2153],
        [0.3274, 0.3610, 0.4204, 0.5046],
        [0.5916, 0.6730, 0.8254, 1.0]
    ]]) * 15/16 * 2 * np.pi

    # define expect phase state index corresponding to each phase value above
    phase_idx_expected = np.array([[
        [0, 1, 2, 3],
        [4, 5, 6, 7],
        [8, 9, 10, 11],
        [12, 13, 14, 15]
    ]])
    
    # define expected memory values for each displacement level
    memory_expected = np.array([[
        [3, 2, 1, 7],
        [0, 6, 5, 4],
        [11, 10, 9, 8],
        [15, 14, 13, 12]
    ]])
    
    # define expected bits we should get for the given phase map, which accounts for memory mapping and bit layout on electrodes under PLM mirrors
    bits_expected_unflipped = np.array([[
        [1, 0, 1, 0, 0, 0, 1, 0],
        [1, 0, 0, 0, 1, 0, 1, 1],
        [0, 0, 1, 0, 0, 0, 0, 0],
        [0, 0, 0, 1, 1, 1, 0, 1],
        [1, 1, 1, 1, 0, 1, 0, 1],
        [1, 0, 0, 0, 1, 0, 0, 0],
        [1, 1, 1, 1, 0, 1, 0, 1],
        [1, 1, 0, 1, 1, 1, 0, 1]
    ]], dtype=np.uint8)
    bits_expected = np.flip(bits_expected_unflipped, -1)  # flip along column axis (horizontal) for p67 plm

    plm = PLM.from_db('p67')
    
    # test individual functions related to calculating bits from phase map
    phase_idx = plm.quantize(phase)
    assert np.array_equal(phase_idx, phase_idx_expected)
    memory = plm.memory_lut[phase_idx]
    assert np.array_equal(memory, memory_expected)
    bits = plm.bitpack(phase_idx)
    assert np.array_equal(bits, bits_expected)
    
    # test full algorithm
    out = plm.process_phase_map(phase, replicate_bits=False, enforce_shape=False)
    assert np.array_equal(out, bits_expected)
