# backend/app/connectors/__init__.py
def __getattr__(name):
    if name == 'config_db':
        from . import config_db as _config_db
        return _config_db
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

__all__ = ['config_db']