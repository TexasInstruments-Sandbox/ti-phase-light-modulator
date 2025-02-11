"""
This is the main module defining the PLM class. The PLM class leverages the `param` library to define parameters describing a PLM, such as its resolution, pixel pitch, phase state levels, etc. Each parameter is defined at the class level and includes default values and detailed documentation about what that parameter is. The `param` library enforces type checking and provides a nice dependency graph through function decorators
"""
import importlib.metadata
import param
import numpy as np
from .util import TIPLMException, TWO_PI, bitstack

__version__ = importlib.metadata.version(__package__ or __name__)


class PLM(param.Parameterized):
    """Base class describing a TI PLM device"""
    
    shape = param.XYCoordinates(
        label='Shape (rows, columns)',
        doc='Shape of PLM as (rows, columns)'
    )
    
    pitch = param.XYCoordinates(
        label='Micromirror Pitch (m))',
        doc='Pitch of micromirrors as (vertical, horizontal). Units are meters. Order of dimensions matches row-major format of other PLM params.'
    )
    
    phase_range = param.Range(
        label='Phase Range',
        doc='Min and max phase values',
        default=(0, TWO_PI)
    )
    
    displacement_ratios = param.Array(
        label='Displacement Ratios',
        doc='Numpy array of mirror displacement ratios in the range [0, 1]. Displacement ratios should be monotonically increasing. Ensure order matches that of `memory_lut` param.',
        default=np.array([])
    )
    
    memory_lut = param.Array(
        label='Memory LUT',
        doc='Lookup table for values that are written to the PLM electrodes under each mirror corresponding to each displacement level. These values are typically not in monotonically increasing order.',
        default=np.array([])
    )
    
    bitpack_layout = param.Array(
        label='Bitpack Layout',
        doc='2D array defining physical locations of each electrode under the PLM mirror. E.g. [[2, 3], [0, 1]] defines a 2x2 electrode layout where the top-left is bit 2, top-right is bit 3, bottom-left is bit 0, and bottom-right is bit 1.',
        default=np.array([]),
    )
    
    data_flip = param.Tuple(
        label='Data Flip (vertical, horizontal)',
        doc='2-tuple indicating whether or not to flip PLM memory cell data. E.g. (False, True) would indicate a flip along the column dimension only (horizontal flip). (True, False) would result in a vertical flip. Note that this is different than an image flip, which should be applied to the image before CGH calculation.',
        default=(False, False)
    )
    
    def __init__(self, **params):
        self._phase_buckets = None
        self._n_bits = 0
        self._flip_dims = []  # array of dimension indices that should be flipped after final bitmap is calculated
        
        super().__init__(**params)
        
        if len(self.bitpack_layout.shape) != 2:
            raise TIPLMException('`bitpack_layout` must be 2D')
    
    @param.depends('displacement_ratios', 'phase_range', watch=True, on_init=True)
    def _update_phase_buckets(self):
        """Cache the phase bucket array for use in the quantize operation.
        
        This function will be run automatically any time any of the @param.depends decorator parameters are updated.
        """
        
        if self.displacement_ratios is None or len(self.displacement_ratios) == 0 or not all(np.diff(self.displacement_ratios) > 0):
            raise TIPLMException('`displacement_ratios` array must be monotonically increasing')
        
        # save number of bits for later use by other class methods
        self._n_bits = len(self.displacement_ratios)
        
        # scale displacements between phase_range min and max such that the full displacement range represents one less bit than the available bit depth
        phase_disp = self.phase_range[0] + (self.displacement_ratios * (self._n_bits - 1) / self._n_bits) * (self.phase_range[-1] - self.phase_range[0])
        phase_disp = np.hstack([phase_disp, self.phase_range[-1]])

        # use average value of each phase level and the level above it to create buckets
        self._phase_buckets = (phase_disp[:-1] + phase_disp[1:]) / 2
    
    def quantize(self, phase_map):
        """Quantize phase data into a fixed number of phase states based on this device's displacement table

        Args:
            phase_map (ndarray): Phase data in floating point format. Data range should match that of `phase_range` param.

        Returns:
            ndarray: Array containing phase state index values corresponding to each input phase value. Range of outputs will be [0 n_states] where n_states is determined by the number of phase states the current device supports.
        """
        phase_state_idx = np.digitize(phase_map, self._phase_buckets) % self._n_bits
        return phase_state_idx
    
    def bitpack(self, phase_state_idx):
        """Convert phase state index to electrode layout array based on the current device's memory map and bitpack layout.

        Args:
            phase_state_idx (ndarray): Array of phase state index values. Must be at least 2D. If >2D, last 2 dimensions will be treated as PLM row and column. E.g. if operating on data for multiple channels, dimensions should be channel, row, column. Supports prepending arbitrary dimensions as long as last 2 are row and column.

        Returns:
            ndarray: Uint8 array of binary encoded phase index values. Output dimensions will be a function of the bitpacking layout. E.g. if 2x2 bitpacking layout is used, the last 2 output dimensions will be 2x rows and columns of input.
        """
        
        # index into `memory_lut` using `phase_state_idx` array. resulting `memory` array will have same shape as `phase_state_idx`.
        memory = self.memory_lut[phase_state_idx]
        
        # broadcast `memory` and `bitpack_layout` with bitwise_right_shift so all elements of `memory` are shifted by all values in `bitpack_layout`
        # resulting array will have 2 additional dimensions added to the end representing the 2 dimensions of bitpack_layout
        # at the same time, use `& 1` to mask everything except LSB
        out = np.bitwise_right_shift(memory[..., None, None], self.bitpack_layout.astype(np.uint8)).astype(np.uint8) & 1
        
        # calculate new shape of final output by multiplying the last 2 dimensions by the shape of bitpack_layout
        new_shape = np.concat([np.array(memory.shape)[:-2], np.multiply(memory.shape[-2:], self.bitpack_layout.shape)])
        
        # rearrange array axes so when we call reshape we end up with groups of NxM bits in the order defined by bitpack_layout array
        out = np.swapaxes(out, -2, -3).reshape(new_shape)
        
        # flip array along axes indicated in `data_flip` parameter
        # `flip` function calls for dimension indices, so we need to create an array of index values corresponding to all dimensions that are True in data_flip
        # use reverse indexing starting from -2 to only operate on last 2 dimensions (row, column)
        out = np.flip(out, [-2 + idx for idx, flip in enumerate(self.data_flip) if flip])
        
        return out

    def process_phase_map(self, phase_map, replicate_bits=True, enforce_shape=True):
        """Process an array of phase data into a bitmap appropriate for displaying on this PLM device. This function handles quantization and bitpacking of data.

        Args:
            phase_map (ndarray): Array containing phase data in the range [0, 2pi). Array should have 3 dimensions: channel, row, column
            replicate_bits (bool, optional): Whether or not to multiply the final bitplane by 255 (0b11111111) so that the same CGH will be displayed for the full frame time. Defaults to True.
            enforce_shape (bool, optional): Whether or not to make sure the input phase map has the correct resolution. Defaults to True.

        Raises:
            TIPLMException: Incorrect phase map resolution

        Returns:
            ndarray: Quantized and bitpacked data based on the provided phase map, optionally replicated across all bits to fill the full frame time with the same CGH.
        """
        if enforce_shape and (len(phase_map.shape) < 2 or phase_map.shape[-2] != self.shape[0] or phase_map.shape[-1] != self.shape[1]):
            raise TIPLMException(f'Phase map shape ({phase_map.shape}) does not match device shape ({self.shape}).')
        
        out = self.bitpack(self.quantize(phase_map))
        
        if replicate_bits:
            out *= 255
        
        return out

    @staticmethod
    def bitstack(bitmaps):
        return bitstack(bitmaps)
    
    @classmethod
    def from_db(cls, name, **params):
        """Create a PLM instance by searching the database for a given device name.

        Args:
            name (str): Device name to search for in database
            **params: Custom param values to override deserialized or default values.
        """
        from .db import get_db, get_device_list
        db = get_db()
        if name in db:
            db_params = cls.param.deserialize_parameters(db[name])  # get dict of params deserialized from json string
            obj = cls(**db_params | params)  # create new PLM object with param values
            for p in db_params.keys():
                obj.param[p].constant = True  # set db params to constant
            return obj
        else:
            raise TIPLMException(f'Unrecognized device name. Please select from one of {get_device_list()}')
