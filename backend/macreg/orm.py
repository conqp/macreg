"""Object relational mappings."""

from datetime import datetime
from ipaddress import IPv4Network
from itertools import chain
from os import linesep
from re import compile  # pylint: disable=W0622
from uuid import uuid4

from httpam import NoSuchSession
from peewee import BooleanField
from peewee import CharField
from peewee import DateTimeField
from peewee import FixedCharField
from peewee import UUIDField
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
NETWORK = IPv4Network(CONFIG['network']['network'])


def create_tables(safe=True):
    """Creates the respective tables."""

    for model in MODELS:
        model.create_table(safe=safe)


class _MacRegModel(JSONModel):  # pylint: disable=R0903
    """Base model."""

    class Meta:     # pylint: disable=C0111,R0903
        database = DATABASE


class Session(_MacRegModel):
    """The session storage."""

    class Meta:     # pylint: disable=C0111,R0903
        database = DATABASE

    token = UUIDField(default=uuid4)
    user = CharField(255)
    start = DateTimeField(default=datetime.now)
    end = DateTimeField()

    @classmethod
    def open(cls, user, duration):
        """Opens a session for the respective user."""
        session = cls()
        session.user = user.pw_name
        session.end = datetime.now() + duration
        session.save()
        return session

    @classmethod
    def by_token(cls, token):
        """Returns a session by its token."""
        try:
            return cls.get(cls.token == token)
        except cls.DoesNotExist:
            raise NoSuchSession()

    @classmethod
    def by_user(cls, user):
        """Yields sessions of the respective user."""
        return cls.select().where(cls.user == user.pw_name)

    @property
    def valid(self):
        """Validates the session."""
        return self.start <= datetime.now() <= self.end

    def refresh(self, duration):
        """Renews a session."""
        self.end = datetime.now() + duration
        self.save()
        return self

    def close(self):
        """Closes the session."""
        return self.delete_instance()


class MACList(_MacRegModel):
    """A white list for MAC addresses."""

    class Meta:     # pylint: disable=C0111,R0903
        database = DATABASE
        table_name = 'mac_list'

    user_name = CharField(255, unique=True)
    mac_address = FixedCharField(17, unique=True)
    ipv4address = IPv4AddressField(null=True)
    timestamp = DateTimeField(default=datetime.now)
    enabled = BooleanField(default=False)
    description = CharField(255)

    def __str__(self):
        """Returns the ID and MAC address."""
        return '\t'.join(str(column) for column in self.columns)

    @classmethod
    def from_json(cls, json, user_name, skip=IGNORE_FIELDS, **kwargs):
        """Creates a new record from a JSON-ish dict."""
        mac_address = json.pop('macAddress')

        if MAC_PATTERN.fullmatch(mac_address) is None:
            raise InvalidMacAddress()

        mac_address = mac_address.replace('-', ':').upper()     # Normalize.

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
        ipv4addresses = frozenset(cls.ipv4addresses())

        for ipv4address in NETWORK:
            if ipv4address not in ipv4addresses:
                return ipv4address

        raise NetworkExhausted()

    @classmethod
    def list_enabled(cls):
        """Yields enabled records."""
        return cls.select().where(~ cls.ipv4address >> None)

    @classmethod
    def dhcpd_conf(cls, prefix=None, suffix=None, spacing=2*linesep):
        """Returns an appropriate dhcpd.conf."""
        prefix = () if prefix is None else (prefix,)
        suffix = () if suffix is None else (suffix,)
        records = (record.to_dhcpd() for record in cls.list_enabled())
        return spacing.join(chain(prefix, records, suffix))

    @property
    def columns(self):
        """Returns the record's columns."""
        return (self.id, self.user_name, self.mac_address, self.ipv4address,
                self.timestamp, self.enabled, self.description)

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

        self.enabled = True
        self.save()
        return self.ipv4address

    def disable(self):
        """Disables the MAC address."""
        self.enabled = False
        self.ipv4address = None     # Free IP address.
        self.save()

    def to_dhcpd(self):
        """Returns a string for a dhcpd.conf file entry."""
        if self.ipv4address is None:
            raise NotActivated()

        return DHCPD_TEMPLATE.format(
            comment=self.comment, name=self.name,
            mac_address=self.mac_address, ipv4address=self.ipv4address)


MODELS = (Session, MACList)
