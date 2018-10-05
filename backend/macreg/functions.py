"""Common functions."""


__all__ = ['comment']


def _comment_lines(string):
    """Normalizes a string for compliance
    with dhcpd.conf comments.
    """

    for line in string.split('\n'):
        line = line.strip()
        yield f'# {line}'


def comment(string):
    """Converts a string to dhcpd.conf comment lines."""

    return '\n'.join(_comment_lines(string))
