"""Translation handlers loaded on demand.

Some handlers, notably PDF, initialize large optional runtimes at import time.
Keeping package imports lazy prevents unrelated database/API helpers from
opening those runtimes and makes worker startup deterministic.
"""

from importlib import import_module


_MODULES = {
    'word',
    'excel',
    'powerpoint',
    'pdf',
    'txt',
    'csv_handle',
    'md',
    'html',
    'to_translate',
    'common',
    'db',
    'docx_inline',
}

__all__ = sorted(_MODULES)


def __getattr__(name):
    if name in _MODULES:
        module = import_module(f'{__name__}.{name}')
        globals()[name] = module
        return module
    raise AttributeError(f'module {__name__!r} has no attribute {name!r}')
