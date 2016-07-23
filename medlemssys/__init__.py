try:
    VERSION = __import__('pkg_resources') \
        .get_distribution('medlemssys').version
except Exception as e:
    VERSION = 'unknown'

__version__ = VERSION
