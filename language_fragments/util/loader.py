import logging
import sys
import os
import re
import codecs
import imp


def load_module(module_path):
    """load a particular zubr module using format:
    zubr.module1.module12.ect.. 

    :param module_path: path of module to be loaded
    :type module_path: str
    :returns: loaded module
    :rtype: module 
    """
    mod = __import__(module_path)
    for c in module_path.split('.')[1:]:
        mod = getattr(mod,c)
    return mod
