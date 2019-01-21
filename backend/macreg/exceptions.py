"""Common exceptions."""


__all__ = [
    'InvalidSessionToken',
    'NotLoggedIn',
    'NetworkExhausted',
    'AlreadyRegistered',
    'InvalidMacAddress',
    'NotActivated']


class InvalidSessionToken(ValueError):
    """Indicates an invalid value for the session ID."""


class NotLoggedIn(Exception):
    """Indicates that the user is not logged in."""


class NetworkExhausted(Exception):
    """Indicates that no more IPv4 addresses are available."""


class AlreadyRegistered(Exception):
    """Indicates that the respective MAC
    address has already been registered.
    """


class InvalidMacAddress(Exception):
    """Indicates that an invalid mac address has been provided."""


class NotActivated(Exception):
    """Indicates that the registered MAC
    address has not yet been activated.
    """
