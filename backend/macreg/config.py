"""Service configuration parser."""

from configparser import ConfigParser


__all__ = ['CONFIG']


CONFIG = ConfigParser()
CONFIG.read('/etc/macreg.conf')
