"""WSGI service."""

from uuid import UUID

from flask import Flask, request, jsonify
from httpam import InvalidUserNameOrPassword, SessionExpired, SessionManager

from macreg.config import CONFIG
from macreg.orm import MacWhitelist


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


@APPLICATION.route('/login', methods=['POST'])
def login():
    """Performa a login."""

    user_name = request.json.get('userName')
    passwd = request.json.get('passwd')

    if user_name is None or passwd is None:
        return ('No user name and / or password provided.', 400)

    try:
        session = SESSION_MANAGER.login(user_name, passwd)
    except InvalidUserNameOrPassword:
        return ('Invalid user name or password.', 400)

    return jsonify(session)


@APPLICATION.route('/mac', methods=['GET'])
def list_macs():
    """Lists the MAC addresses of the respective user."""

    user = _get_user()

    if user.pw_name in CONFIG['wsgi']['admins'].split():
        records = MacWhitelist
    else:
        records = MacWhitelist.select().where(
            MacWhitelist.user_name == user.pw_name)

    return jsonify([record.to_json() for record in records])


@APPLICATION.route('/mac', methods=['POST'])
def submit_mac():
    """Submit a MAC address."""

    user = _get_user()
    record = MacWhitelist.from_json(user.pw_name, request.json)
    record.save()
    return 'MAC address added.'
