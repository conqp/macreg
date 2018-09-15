/*
    (C) 2018 Richard Neumann <mail at richard dash neumann period de>

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
*/
'use strict';

var macreg = macreg || {};

macreg.BASE_URL = '';   // !!! SET THIS !!!
macreg.LOGIN_URL = macreg.BASE_URL + '/login';
macreg.SUBMIT_URL = macreg.BASE_URL + '/mac';
macreg.sessionTokenKey = 'macreg.sessionToken';


/*
  Makes a request returning a promise.
*/
macreg.makeRequest = function (method, url, data=null, ...headers) {
  function executor (resolve, reject) {
    function onload () {
      if (this.status >= 200 && this.status < 300) {
        resolve(xhr.response);
      } else {
        reject({
          status: this.status,
          statusText: xhr.statusText
        });
      }
    };

    function onerror () {
      reject({
        status: this.status,
        statusText: xhr.statusText
      });
    };

    var xhr = new XMLHttpRequest();
    xhr.open(method, url);

    for (var header of headers) {
      xhr.setRequestHeader(...header);
    }

    xhr.onload = onload;
    xhr.onerror = onerror;

    if (data == null) {
      xhr.send();
    } else {
      xhr.send(data);
    }
  };

  return new Promise(executor);
}


/*
  Attempts an automatic login.
*/
macreg.autoLogin = function () {
  var sessionToken = localStorage.getItem(macreg.sessionTokenKey);

  if (sessionToken == null) {
    console.log('No session stored.');
    return;
  }

  var header = ['Content-Type', 'application/json'];
  var payload = {session: sessionToken};
  var data = JSON.stringify(payload);
  macreg.makeRequest('PUT', macreg.LOGIN_URL, data, header).then(
    function (session) {
      localStorage.setItem(macreg.sessionTokenKey, session.token);
      window.location = 'submit.html';
    },
    function (error) {
      console.log('Autologin failed:\n' + JSON.stringify(error));
    }
  );
};


/*
  Performs a login.
*/
macreg.login = function () {
  var userName = document.getElementById('userName').value;
  var password = document.getElementById('password').value;
  var header = ['Content-Type', 'application/json'];
  var payload = {userName: userName, password: password};
  var data = JSON.stringify(payload);
  return macreg.makeRequest('POST', macreg.LOGIN_URL, data, header).then(
    function () {
      window.location = 'submit.html';
    },
    function (error) {
      console.log('Login failed:\n' + JSON.stringify(error));
      alert('Invalid user name or password.');
    }
  );
};
