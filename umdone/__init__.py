import os
import tempfile


__version__ = '0.1.dev0'

from xonsh.main import setup
setup(env={
    'UMDONE_CACHE_DIR': os.environ.get('UMDONE_CACHE_DIR',
                                       os.path.join(tempfile.gettempdir(),
                                                    'umdone-cache'))
    })
del setup
