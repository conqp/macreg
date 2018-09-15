"""WSGI service."""

from traceback import format_exc
from uuid import UUID

from flask import Flask, request, jsonify
from httpam import InvalidUserNameOrPassword, SessionExpired, SessionManager

from macreg.config import CONFIG
from macreg.exceptions import InvalidSessionToken, NotLoggedIn, \
    InvalidMacAddress, AlreadyRegistered, NetworkExhausted
from macreg.orm import Session, MACList


__all__ = ['APPLICATION']


ADMINS = CONFIG.get('admins', ())
SESSION_MANAGER = SessionManager(Session, config='/etc/macreg.json')
APPLICATION = Flask('macreg')


def _get_user():
    """Returns the logged-in user."""

    try:
        token = request.args['session']
    except KeyError:
        raise NotLoggedIn()

    try:
        token = UUID(token)
    except (TypeError, ValueError):
        raise InvalidSessionToken()

    return SESSION_MANAGER.get(token).user


@APPLICATION.errorhandler(SessionExpired)
def _session_expired(_):
    """Returns an appropriate error message."""

    return ('Session expired.', 400)


@APPLICATION.errorhandler(InvalidSessionToken)
def _invalid_session_token(_):
    """Returns an appropriate error message."""

    return ('Invalid session token.', 400)


@APPLICATION.errorhandler(NotLoggedIn)
def _not_logged_in(_):
    """Returns an appropriate error message."""

    return ('Not logged in.', 400)


@APPLICATION.errorhandler(InvalidMacAddress)
def _invalid_mac_address(_):
    """Returns an appropriate error message."""

    return ('Invalid MAC address specified.', 400)


@APPLICATION.errorhandler(NetworkExhausted)
def _network_exhausted(_):
    """Returns an appropriate error message."""

    return ('No free IP addresses left.', 400)


@APPLICATION.errorhandler(AlreadyRegistered)
def _already_registered(_):
    """Returns an appropriate error message."""

    return ('This MAC address has already been registered.', 400)


@APPLICATION.errorhandler(Exception)
def _internal_server_error(exception):
    """Returns an appropriate error message."""

    return (format_exc() + '\n' + str(exception), 400)


@APPLICATION.route('/login', methods=['POST'])
def login():
    """Performa a login."""

    user_name = request.json.get('userName')
    passwd = request.json.get('passwd')

    if not user_name or not passwd:
        return ('No user name and / or password provided.', 400)

    try:
        session = SESSION_MANAGER.login(user_name, passwd)
    except InvalidUserNameOrPassword:
        return ('Invalid user name or password.', 400)

    return jsonify(session.to_json())


@APPLICATION.route('/login', methods=['PUT'])
def refresh_session():
    """Performa a login."""

    token = request.json['session']

    try:
        token = UUID(token)
    except (TypeError, ValueError):
        raise InvalidSessionToken()

    session = SESSION_MANAGER.refresh(token)
    return jsonify(session.to_json())


@APPLICATION.route('/mac', methods=['GET'])
def list_macs():
    """Lists the MAC addresses of the respective user."""

    user = _get_user()

    if user in ADMINS:
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
    return 'MAC address added.'


@APPLICATION.route('/mac', methods=['PATCH'])
def enable_mac():
    """Submit a MAC address."""

    user = _get_user()

    if user not in ADMINS:
        return ("You're not an admininistrator. Sorry.", 403)

    mac_address = request.json['macAddress']
    record = MACList.get(MACList.mac_address == mac_address)
    ipv4address = record.enable()
    return f'IPv4 address assigned to MAC address: {ipv4address}.'
