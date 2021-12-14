from datetime import datetime
from shutil import rmtree
import os

def make_experiment_directory(path='',config=None,default_dir='_runs'):
    """build a new directory from path, if
    no place is provided, create a random directory inside
    zubr source examples/results directory

    :param path: desired location of new directory (possibly none) 
    :type path: str
    :returns: full path of new directory
    :rtype: str
    :raises: OsUtilError
    """
    directory = path
    
    if not path:
        timestamp = datetime.now().strftime('%Y-%m-%dT%H-%M-%S-%f')
        directory = os.path.join(default_dir,timestamp)
    directory = os.path.abspath(directory) 
    if os.path.isdir(directory) and not config.override and not config.cloud:
        raise ValueError(
            'directory already exists, use --override option: %s'
            % directory)
    elif os.path.isdir(directory) and not config.cloud: 
        rmtree(directory)
    if not config.cloud: 
        os.makedirs(directory)
    if config:
        config.wdir = directory 
    return directory
