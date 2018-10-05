"""Object relational mappings."""

from datetime import datetime
from ipaddress import IPv4Network
from re import compile  # pylint: disable=W0622

from httpam import SessionBase
from peewee import CharField, DateTimeField, FixedCharField
from peeweeplus import IPv4AddressField, JSONModel, MySQLDatabase

from macreg.config import CONFIG
from macreg.exceptions import AlreadyRegistered
from macreg.exceptions import InvalidMacAddress
from macreg.exceptions import NetworkExhausted
from macreg.exceptions import NotActivated
from macreg.functions import comment


__all__ = ['create_tables', 'Session', 'MACList']


DATABASE = MySQLDatabase.from_config(CONFIG['db'])
DHCPD_TEMPLATE = '''{comment}
host {name} {{
    hardware ethernet {mac_address};
    fixed-address {ipv4address};
}}'''
IGNORE_FIELDS = ('user_name', 'mac_address', 'ipv4address', 'timestamp')
MAC_PATTERN = compile('^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$')
NETWORK = IPv4Network(CONFIG['network'])


def create_tables(safe=True):
    """Creates the respective tables."""

    for model in MODELS:
        model.create_table(safe=safe)


class _MacRegModel(JSONModel):
    """Base model."""

    class Meta:     # pylint: disable=C0111,R0903
        database = DATABASE


class Session(_MacRegModel, SessionBase):
    """The session storage."""

    class Meta:     # pylint: disable=C0111,R0903
        database = DATABASE


class MACList(_MacRegModel):
    """A white list for MAC addresses."""

    class Meta:     # pylint: disable=C0111,R0903
        database = DATABASE
        table_name = 'mac_list'

    user_name = CharField(255, unique=True)
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
            record = cls.get(cls.mac_address == mac_address)
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

    @classmethod
    def enabled(cls):
        """Yields enabled records."""
        return cls.select().where(~ cls.ipv4address >> None)

    @classmethod
    def dhcpd_conf(cls):
        """Returns an appropriate dhcpd.conf."""
        return '\n\n'.join(record.to_dhcpd() for record in cls.enabled())

    @property
    def name(self):
        """Returns a unique name for this record."""
        return f'{self.user_name}-{self.id}'

    @property
    def comment(self):
        """Returns a comment for this record."""
        return f'# {self.timestamp}\n' + comment(self.description)

    def enable(self):
        """Enables the record."""
        if self.ipv4address is None:
            self.ipv4address = type(self).free_ipv4address()
            self.save()

        return self.ipv4address

    def to_dhcpd(self):
        """Returns a string for a dhcpd.conf file entry."""
        if self.ipv4address is None:
            raise NotActivated()

        return DHCPD_TEMPLATE.format(
            comment=self.comment, name=self.name,
            mac_address=self.mac_address, ipv4address=self.ipv4address)


MODELS = (Session, MACList)
