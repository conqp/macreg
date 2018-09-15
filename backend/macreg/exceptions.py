"""Common exceptions."""

__all__ = ['NetworkExhausted', 'AlreadyRegistered', 'InvalidMacAddress']


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
