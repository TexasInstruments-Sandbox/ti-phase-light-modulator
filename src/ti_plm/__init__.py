"""
This is the main module defining the PLM class. The PLM class leverages the 'param' library to parameterize a PLM device, such as its resolution, pixel pitch, phase state levels, etc. Each parameter is defined at the class level and includes default values and detailed documentation about what that parameter is. The `param` library enforces type checking and makes it easy to define a dependency graph through function decorators.
"""
import importlib.metadata
import param
import numpy as np
from .util import TIPLMException, TWO_PI, bitpack

__version__ = importlib.metadata.version(__package__ or __name__)


class PLM(param.Parameterized):
    """Base class defining intrinsic properties of a PLM device."""
    
    shape = param.XYCoordinates(
        label='Shape (rows, columns)',
        doc='Resolution of PLM as (rows, columns)'
    )
    
    pitch = param.XYCoordinates(
        label='Pitch (m)',
        doc='Vertical and horizontal pitch of micromirrors in meters. Order (vertical, horizontal) matches row-major format of arrays and shape param.'
    )
    
    phase_range = param.Range(
        label='Phase Range',
        doc='Min and max phase values',
        default=(0, TWO_PI)
    )
    
    displacement_ratios = param.Array(
        label='Displacement Ratios',
        doc='Numpy array of mirror displacement ratios in the range [0, 1]. List should include 0.0 as first element and 1.0 as last element. Displacement ratios should be monotonically increasing. Ensure order matches that of `memory_lut` param.',
        default=np.array([])
    )
    
    memory_lut = param.Array(
        label='Memory LUT',
        doc='Lookup table for values that are written to the PLM electrodes under each mirror corresponding to each displacement level. These values are typically not in monotonically increasing order.',
        default=np.array([])
    )
    
    electrode_layout = param.Array(
        label='Electrode Layout',
        doc='2D array defining physical locations of each electrode under the PLM mirror. E.g. [[2, 3], [0, 1]] defines a 2x2 electrode layout where the top-left is bit 2, top-right is bit 3, bottom-left is bit 0, and bottom-right is bit 1.',
        default=np.array([[]]),
    )
    
    data_flip = param.Tuple(
        label='Data Flip (vertical, horizontal)',
        doc='2-tuple indicating whether or not to flip PLM memory cell data. E.g. (False, True) would indicate a flip along the column dimension only (horizontal flip). (True, False) would result in a vertical flip. Note that this is different than an image flip, which should be applied to the image before CGH calculation.',
        default=(False, False)
    )
    
    def __init__(self, **params):
        
        # init cache of phase buckets and number of bits
        self._phase_buckets = None
        self._n_bits = 0
        
        # init parent class
        super().__init__(**params)
        
        # ensure electrode_layout is exactly 2D
        if len(self.electrode_layout.shape) != 2:
            raise TIPLMException('`electrode_layout` must be 2D')
    
    @param.output(param.Number(label='Size (m)', doc='Active array dimensions (height, width) in meters'))
    @param.depends('shape', 'pitch')
    def size(self):
        return np.multiply(self.shape, self.pitch)
    
    @param.output(param.Number(label='Area (m²)', doc='Active array area in square meters'))
    @param.depends('size')
    def area(self):
        return np.prod(self.size())
    
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
    
    def electrode_map(self, phase_state_idx):
        """Convert phase state index to electrode layout array based on the current device's memory map and electrode map layout.

        Args:
            phase_state_idx (ndarray): Array of phase state index values. Must be at least 2D. If >2D, last 2 dimensions will be treated as PLM row and column. E.g. if operating on data for multiple channels, dimensions should be channel, row, column. Supports prepending arbitrary dimensions as long as last 2 are row and column.

        Returns:
            ndarray: Uint8 array of binary encoded phase index values. Output dimensions will be a function of the electrode layout. E.g. if 2x2 electrode layout is used, the last 2 output dimensions will be 2x rows and columns of input.
        """
        
        # index into `memory_lut` using `phase_state_idx` array. resulting `memory` array will have same shape as `phase_state_idx`.
        memory = self.memory_lut[phase_state_idx]
        
        # broadcast `memory` and `electrode_layout` with bitwise_right_shift so all elements of `memory` are shifted by all values in `electrode_layout`
        # resulting array will have 2 additional dimensions added to the end representing the 2 dimensions of electrode_layout
        # at the same time, use `& 1` to mask everything except LSB
        out = np.bitwise_right_shift(memory[..., None, None], self.electrode_layout.astype(np.uint8)).astype(np.uint8) & 1
        
        # calculate new shape of final output by multiplying the last 2 dimensions by the shape of electrode_layout
        new_shape = np.concat([np.array(memory.shape)[:-2], np.multiply(memory.shape[-2:], self.electrode_layout.shape)])
        
        # rearrange array axes so when we call reshape we end up with groups of NxM bits in the order defined by electrode_layout array
        out = np.swapaxes(out, -2, -3).reshape(new_shape)
        
        # flip array along axes indicated in `data_flip` parameter
        # `flip` function calls for dimension indices, so we need to create an array of index values corresponding to all dimensions that are True in data_flip
        # use reverse indexing starting from -2 to only operate on last 2 dimensions (row, column)
        out = np.flip(out, [-2 + idx for idx, flip in enumerate(self.data_flip) if flip])
        
        return out

    def process_phase_map(self, phase_map, replicate_bits=True, enforce_shape=True):
        """Process an array of phase data into a bitmap appropriate for displaying on this PLM device. This function handles quantization and electrode mapping of data.

        Args:
            phase_map (ndarray): Array containing phase data in the range [0, 2pi). Array can have 3 or more dimensions (e.g. channel, row, column).
            replicate_bits (bool, optional): Whether or not to multiply the final bitplane by 255 (0b11111111) so that the same CGH will be displayed for the full frame time. Defaults to True.
            enforce_shape (bool, optional): Whether or not to make sure the input phase map has the correct resolution. Defaults to True.

        Raises:
            TIPLMException: Incorrect phase map resolution

        Returns:
            ndarray: Quantized and electrode mapped data based on the provided phase map, optionally replicated across all bits to fill the full frame time with the same CGH.
        """
        if enforce_shape and (len(phase_map.shape) < 2 or phase_map.shape[-2] != self.shape[0] or phase_map.shape[-1] != self.shape[1]):
            raise TIPLMException(f'Phase map shape ({phase_map.shape}) does not match device shape ({self.shape}).')
        
        out = self.electrode_map(self.quantize(phase_map))
        
        if replicate_bits:
            out *= 255
        
        return out

    @staticmethod
    def bitpack(bitmaps):
        """Combine multiple binary CGHs into a single 8- or 24-bit image. See global `bitpack` function for usage details."""
        return bitpack(bitmaps)
    
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
