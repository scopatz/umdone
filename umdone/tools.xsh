"""Generic utlities for umdone"""
import os

from joblib import Memory


os.makedirs($UMDONE_CACHE_DIR, exist_ok=True)
MEM = Memory(location=$UMDONE_CACHE_DIR, verbose=100)
cache = MEM.cache
