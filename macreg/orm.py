"""Object relational mappings."""

from peewee import CharField, FixedCharField

from peeweeplus import MySQLDatabase, JSONModel


class NetworkExhausted(Exception):
    """Indicates that no more IPv4 addresses are available."""
    
    pass


class MacWhitelist(JSONModel):
    """A white list for MAC addresses."""

    user_name = CharField(255)
    first_name = CharField(255)
    last_name = CharField(255)
    description = CharField(255)
    mac_address = FixedCharField(17)
    ipv4address = IPv4AddressField(null=True)

    @classmethod
    def ipv4addresses(cls):
        """Yields the used IPv4 addresses."""
        for record in cls:
            yield record.ipv4address
            
    @classmethod
    def free_ipv4address(cls, network):
        """Returns the lowest freee IPv4 address."""
        ipv4addresses = set(cls.ipv4addresses())
        
        for ipv4address in network:
            if ipv4address not in ipv4addresses:
                return ipv4address
            
        raise NetworkExhausted()
            
    def enable(self):
        """Enables the record."""
        if self.ipv4address is None:
            self.ipv4address = type(self).free_ipv4address()  
