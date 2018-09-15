"""Object relational mappings."""

from datetime import datetime
from ipaddress import IPv4Network
from re import compile

from peewee import CharField, FixedCharField, DateTimeField

from peeweeplus import MySQLDatabase, JSONModel, IPv4AddressField

from macreg.config import CONFIG
from macreg.exceptions import InvalidMacAddress, AlreadyRegistered, \
    NetworkExhausted


__all__ = ['MACList']


NETWORK = IPv4Network(CONFIG['network'])
DATABASE = MySQLDatabase.from_config(CONFIG['db'])
MAC_PATTERN = compile('^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$')
IGNORE_FIELDS = ('user_name', 'mac_address', 'ipv4address', 'timestamp')


class MACList(JSONModel):
    """A white list for MAC addresses."""

    class Meta:     # pylint: disable=C0111
        database = DATABASE
        table_name = 'mac_list'

    user_name = CharField(255)
    description = CharField(255)
    mac_address = FixedCharField(17, unique=True)
    ipv4address = IPv4AddressField(null=True)
    timestamp = DateTimeField(default=datetime.now)

    @classmethod
    def from_json(cls, json, user_name, skip=IGNORE_FIELDS, **kwargs):
        """Creates a new record from a JSON-ish dict."""
        mac_address = json.pop('macAddress')

        if MAC_PATTERN.fullmatch(mac_address) is None:
            raise InvalidMacAddress()

        try:
            cls.get(cls.mac_address == mac_address)
        except cls.DoesNotExist:
            record = super().from_json(json, skip=skip, **kwargs)
            record.user_name = user_name
            record.mac_address = mac_address
            return record

        raise AlreadyRegistered()

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
            self.save()

        return self.ipv4address
