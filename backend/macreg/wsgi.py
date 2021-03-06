"""WSGI service."""

from logging import getLogger
from uuid import UUID

from flask import Flask, request, jsonify
from httpam import AuthenticationError, SessionExpired, SessionManager

from macreg.config import CONFIG, admins
from macreg.email import email
from macreg.exceptions import AlreadyRegistered
from macreg.exceptions import InvalidMacAddress
from macreg.exceptions import InvalidSessionToken
from macreg.exceptions import NetworkExhausted
from macreg.exceptions import NotLoggedIn
from macreg.functions import set_session_cookie
from macreg.orm import Session, MACList


__all__ = ['APPLICATION']


APPLICATION = Flask('macreg')
LOGGER = getLogger(__file__)
SESSION_MANAGER = SessionManager(Session, config='/etc/macreg.json')


def _get_session():
    """Returns the current session."""

    cookie = CONFIG['app']['cookie']

    try:
        token = request.cookies[cookie]
    except KeyError:
        raise NotLoggedIn()

    try:
        token = UUID(token)
    except ValueError:
        raise SessionExpired()

    return SESSION_MANAGER.get(token)


def _get_user():
    """Returns the logged-in user."""

    return _get_session().user


def _get_mac_address(ident):
    """Returns the respective MAC address record."""

    user = _get_user()
    condition = MACList.id == ident

    if user not in admins():
        condition &= MACList.user_name == user

    return MACList.get(condition)


@APPLICATION.errorhandler(SessionExpired)
def _session_expired(_):
    """Returns an appropriate error message."""

    return ('Session expired.', 401)


@APPLICATION.errorhandler(InvalidSessionToken)
def _invalid_session_token(_):
    """Returns an appropriate error message."""

    return ('Invalid session token.', 401)


@APPLICATION.errorhandler(NotLoggedIn)
def _not_logged_in(_):
    """Returns an appropriate error message."""

    return ('Not logged in.', 401)


@APPLICATION.errorhandler(InvalidMacAddress)
def _invalid_mac_address(_):
    """Returns an appropriate error message."""

    return ('Invalid MAC address specified.', 400)


@APPLICATION.errorhandler(NetworkExhausted)
def _network_exhausted(_):
    """Returns an appropriate error message."""

    return ('No free IP addresses left.', 507)


@APPLICATION.errorhandler(AlreadyRegistered)
def _already_registered(_):
    """Returns an appropriate error message."""

    return ('This MAC address has already been registered.', 409)


@APPLICATION.errorhandler(MACList.DoesNotExist)
def _no_such_mac(_):
    """Returns an appropriate error message."""

    return ('The requested MAC address does not exist.', 404)


@APPLICATION.after_request
def _set_cookie(response):
    """Sets session cookie on the response."""

    try:
        session = _get_session()
    except (NotLoggedIn, SessionExpired):
        return response

    set_session_cookie(response, session)
    return response


@APPLICATION.route('/login', methods=['POST'])
def login():
    """Performa a login."""

    user_name = request.json.get('userName')
    passwd = request.json.get('passwd')

    if not user_name or not passwd:
        return ('No user name and / or password provided.', 400)

    try:
        session = SESSION_MANAGER.login(user_name, passwd)
    except AuthenticationError:
        return ('Invalid user name or password.', 400)

    response = jsonify(session.to_json())
    set_session_cookie(response, session)
    return response


@APPLICATION.route('/mac', methods=['GET'])
def list_macs():
    """Lists the MAC addresses of the respective user."""

    user = _get_user()

    if user in admins():
        records = MACList
    else:
        records = MACList.select().where(MACList.user_name == user)

    return jsonify([record.to_json() for record in records])


@APPLICATION.route('/mac', methods=['POST'])
def submit_mac():
    """Submit a MAC address."""

    user = _get_user()
    record = MACList.from_json(request.json, user)
    record.save()
    email(record)
    return ('MAC address added.', 201)


@APPLICATION.route('/mac/<int:ident>', methods=['PATCH'])
def toggle_mac(ident):
    """Submit a MAC address."""

    if _get_user() not in admins():
        return ("You're not an admininistrator. Sorry.", 403)

    mac_address = _get_mac_address(ident)

    if mac_address.enabled:
        mac_address.disable()
        return 'Record disabled.'

    ipv4address = mac_address.enable()
    return f'IPv4 address assigned to MAC address: {ipv4address}.'


@APPLICATION.route('/mac/<int:ident>', methods=['DELETE'])
def delete_mac(ident):
    """Deletes a MAC address."""

    mac_address = _get_mac_address(ident)
    mac_address.delete_instance()
    return 'MAC address deleted.'


if __name__ == '__main__':
    APPLICATION.run()
