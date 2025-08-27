from slowapi import Limiter
from slowapi.util import get_remote_address

# Shared limiter for the whole app (60/min default)
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])
