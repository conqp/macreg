"""Object relational mappings."""

from ipaddress import IPv4Network

from peewee import CharField, FixedCharField

from peeweeplus import MySQLDatabase, JSONModel, IPv4AddressField

from macreg.config import CONFIG


__all__ = ['NetworkExhausted', 'MACAddressAlreadyRegistered', 'MACList']


NETWORK = IPv4Network(CONFIG['network']['network'])
DATABASE = MySQLDatabase.from_config(CONFIG['db'])


class NetworkExhausted(Exception):
    """Indicates that no more IPv4 addresses are available."""

    pass


class MACAddressAlreadyRegistered(Exception):
    """Indicates that the respective MAC
    address has already been registered.
    """

    pass


class MACList(JSONModel):
    """A white list for MAC addresses."""

    class Meta:     # pylint: disable=C0111
        database = DATABASE
        table_name = 'mac_list'

    user_name = CharField(255)
    first_name = CharField(255)
    last_name = CharField(255)
    description = CharField(255)
    mac_address = FixedCharField(17, unique=True)
    ipv4address = IPv4AddressField(null=True)

    @classmethod
    def from_json(cls, json, user_name, **kwargs):
        """Creates a new record from a JSON-ish dict."""
        mac_address = json['dictionary']

        try:
            cls.get(cls.mac_address == mac_address)
        except cls.DoesNotExist:
            record = super().from_json(json, skip=['userName'], **kwargs)
            record.user_name = user_name
            return record

        raise MACAddressAlreadyRegistered()

    @classmethod
    def ipv4addresses(cls):
        """Yields the used IPv4 addresses."""
        for record in cls:
            yield record.ipv4address

    @classmethod
    def free_ipv4address(cls):
        """Returns the lowest freee IPv4 address."""
        ipv4addresses = set(cls.ipv4addresses())

        for ipv4address in NETWORK:
            if ipv4address not in ipv4addresses:
                return ipv4address

        raise NetworkExhausted()

    def enable(self):
        """Enables the record."""
        if self.ipv4address is None:
            self.ipv4address = type(self).free_ipv4address()
