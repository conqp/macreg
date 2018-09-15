"""Service configuration parser."""

from configparser import ConfigParser


__all__ = ['CONFIG', 'ADMINS']


CONFIG = ConfigParser()
CONFIG[CONFIG.default_section] = {
    'admins': ''
}
CONFIG.read('/etc/macreg.conf')
ADMINS = CONFIG['wsgi']['admins'].split()
