"""Common exceptions."""


__all__ = [
    'InvalidSessionToken',
    'NotLoggedIn',
    'NetworkExhausted',
    'AlreadyRegistered',
    'InvalidMacAddress']


class InvalidSessionToken(ValueError):
    """Indicates an invalid value for the session ID."""

    pass


class NotLoggedIn(Exception):
    """Indicates that the user is not logged in."""

    pass


class NetworkExhausted(Exception):
    """Indicates that no more IPv4 addresses are available."""

    pass


class AlreadyRegistered(Exception):
    """Indicates that the respective MAC
    address has already been registered.
    """

    pass


class InvalidMacAddress(Exception):
    """Indicates that an invalid mac address has been provided."""

    pass
