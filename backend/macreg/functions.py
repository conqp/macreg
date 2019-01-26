"""Common functions."""

from os import linesep


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


def set_session_cookie(response, session, domain=None):
    """Sets the session cookie."""

    response.set_cookie(
        'session', session.token.hex, expires=session.end, domain=domain,
        secure=True)
    return response
