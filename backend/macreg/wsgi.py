"""WSGI service."""

from uuid import UUID

from flask import Flask, request, jsonify
from httpam import InvalidUserNameOrPassword, SessionExpired, SessionManager

from macreg.config import CONFIG
from macreg.orm import NetworkExhausted, MACAddressAlreadyRegistered, MACList


__all__ = ['APPLICATION']


ADMINS = CONFIG.get('admins', ())
SESSION_MANAGER = SessionManager('/etc/macreg.json')
APPLICATION = Flask('macreg')


class InvalidSessionId(ValueError):
    """Indicates an invalid value for the session ID."""

    pass


def _get_user():
    """Returns the logged-in user."""

    session_id = request.args['session']

    try:
        session_id = UUID(session_id)
    except (TypeError, ValueError):
        raise InvalidSessionId()

    return SESSION_MANAGER.get(session_id).user


@APPLICATION.errorhandler(SessionExpired)
def _session_expired(_):
    """Returns an appropriate error message."""

    return ('Session expired.', 400)


@APPLICATION.errorhandler(InvalidSessionId)
def _invalid_session_id(_):
    """Returns an appropriate error message."""

    return ('Invalid session ID.', 400)


@APPLICATION.errorhandler(NetworkExhausted)
def _invalid_session_id(_):
    """Returns an appropriate error message."""

    return ('No free IP addresses left.', 400)


@APPLICATION.errorhandler(MACAddressAlreadyRegistered)
def _invalid_session_id(_):
    """Returns an appropriate error message."""

    return ('This MAC address has already been registered.', 400)


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

    return jsonify(session)


@APPLICATION.route('/login', methods=['PUT'])
def refresh_session():
    """Performa a login."""

    session_id = request.json['session']

    try:
        session_id = UUID(session_id)
    except (TypeError, ValueError):
        raise InvalidSessionId()

    session = SESSION_MANAGER.refresh(session_id)
    return jsonify(session)


@APPLICATION.route('/mac', methods=['GET'])
def list_macs():
    """Lists the MAC addresses of the respective user."""

    user = _get_user()

    if user.pw_name in ADMINS:
        records = MACList
    else:
        records = MACList.select().where(MACList.user_name == user.pw_name)

    return jsonify([record.to_json() for record in records])


@APPLICATION.route('/mac', methods=['POST'])
def submit_mac():
    """Submit a MAC address."""

    user = _get_user()
    record = MACList.from_json(request.json, user.pw_name)
    record.save()
    return 'MAC address added.'


@APPLICATION.route('/mac', methods=['PATCH'])
def enable_mac():
    """Submit a MAC address."""

    user = _get_user()

    if user.pw_name not in ADMINS:
        return ("You're not an admininistrator. Sorry.", 403)

    mac_address = request.json['macAddress']
    record = MACList.get(MACList.mac_address == mac_address)
    ipv4address = record.enable()
    return f'IPv4 address assigned to MAC address: {ipv4address}.'
