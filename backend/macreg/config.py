"""Service configuration parser."""

from configparser import ConfigParser


__all__ = ['CONFIG', 'admins', 'emails']


CONFIG = ConfigParser()
CONFIG.read('/etc/macreg.conf')


def admins():
    """Yields admin user names."""

    for admin in CONFIG['admins']['admins'].split(','):
        yield admin.strip()


def emails():
    """Yields email addresses."""

    for email in CONFIG['admins']['emails'].split(','):
        yield email.strip()
