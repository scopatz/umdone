"""Generic utlities for umdone"""
from joblib import Memory


MEM = Memory(location=$UMDONE_CACHE_DIR)
cache = MEM.cache
