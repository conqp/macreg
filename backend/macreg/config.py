"""Service configuration parser."""

from json import loads


__all__ = ['CONFIG']


with open('/etc/macreg.json', 'r') as file:
    CONFIG = loads(file.read())
