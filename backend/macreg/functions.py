"""Common functions."""

from os import linesep

from macreg.config import CONFIG


__all__ = ['comment', 'set_session_cookie']


def _comment_lines(string):
    """Normalizes a string for compliance
    with dhcpd.conf comments.
    """

    for line in string.split(linesep):
        line = line.strip()
        yield f'# {line}'


def comment(string):
    """Converts a string to dhcpd.conf comment lines."""

    return '\n'.join(_comment_lines(string))


def set_session_cookie(response, session):
    """Sets the session cookie."""

    response.set_cookie(
        CONFIG['app']['cookie'], session.token.hex, expires=session.end,
        secure=CONFIG.getboolean('app', 'secure'))
    return response
