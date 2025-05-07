from functools import cache
from importlib import resources

data_path = resources.files(__package__ or __name__)


@cache
def get_db():
    """Get device database as dictionary of json strings.
    
    Returns:
        dict: Dictionary of keys (filename without extension) and values (json string) representing all PLMs currently in database
    """
    return {
        f.stem: f.read_text()
        for f in sorted(data_path.glob('*.json'))
    }


@cache
def get_device_list():
    return list(get_db().keys())
