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

macreg.LOGIN_URL = 'login';
macreg.SUBMIT_URL = 'mac';
macreg.sessionTokenKey = 'macreg.sessionToken';


/*
  Returns the query arguments.
*/
macreg.getQueryArgs = function () {
  return '?session=' + localStorage.getItem(macreg.sessionTokenKey);
};


/*
  Makes a request returning a promise.
*/
macreg.makeRequest = function (method, url, data=null, ...headers) {
  function parseResponse (response) {
    try {
      return JSON.parse(response);
    } catch (error) {
      return response;
    }
  };

  function executor (resolve, reject) {
    function onload () {
      if (this.status >= 200 && this.status < 300) {
        resolve({
          response: parseResponse(xhr.response),
          status: this.status,
          statusText: xhr.statusText
        });
      } else {
        reject({
          response: parseResponse(xhr.response),
          status: this.status,
          statusText: xhr.statusText
        });
      }
    };

    function onerror () {
      reject({
          response: parseResponse(xhr.response),
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
};


/*
  Renders the respective records.
*/
macreg._render = function (response) {
  console.log('Rendering records.');
  var container = document.getElementById('records');
  container.innerHTML = '';

  for (var record of response.response) {
    var row = document.createElement('tr');
    var fields = [
      record.timestamp,
      record.userName,
      record.macAddress,
      record.description,
      record.ipv4address || 'N/A'
    ];

    for (var field of fields) {
      var column = document.createElement('td');
      column.textContent = field;
      row.appendChild(column)
    }

    container.appendChild(row);
  }
};


/*
  Runs on submit.html.
*/
macreg.submitInit = function () {
  document.removeEventListener('DOMContentLoaded', macreg.submitInit);
  document.getElementById('btnSubmit').addEventListener('click', function(event){
      event.preventDefault();
  });
  return macreg.render();
};


/*
  Renders the page.
*/
macreg.render = function () {
  return macreg.makeRequest('GET', macreg.SUBMIT_URL + macreg.getQueryArgs()).then(
    macreg._render,
    function (error) {
      console.log('Could not query MAC addresses:\n' + JSON.stringify(error));

      if (error.status == 410) {
        window.location = 'index.html';
        alert(response.response);
      }
    }
  );
};


/*
  Attempts an automatic login.
*/
macreg.autoLogin = function () {
  document.removeEventListener("DOMContentLoaded", macreg.autoLogin);
  document.getElementById('btnLogin').addEventListener('click', function(event){
      event.preventDefault();
  });
  var sessionToken = localStorage.getItem(macreg.sessionTokenKey);

  if (sessionToken == null) {
    console.log('No session stored.');
    return;
  }

  var header = ['Content-Type', 'application/json'];
  var payload = {session: sessionToken};
  var data = JSON.stringify(payload);
  return macreg.makeRequest('PUT', macreg.LOGIN_URL, data, header).then(
    function (response) {
      console.log('Successfully refreshed session.');
      localStorage.setItem(macreg.sessionTokenKey, response.response.token);
      macreg.render();
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
  var payload = {'userName': userName, 'passwd': password};
  var data = JSON.stringify(payload);
  return macreg.makeRequest('POST', macreg.LOGIN_URL, data, header).then(
    function (response) {
      localStorage.setItem(macreg.sessionTokenKey, response.response.token);
      console.log('Redirecting to submit page.');
      window.location = 'submit.html';
    },
    function (error) {
      console.log('Login failed:\n' + JSON.stringify(error));
      alert('Invalid user name or password.');
    }
  );
};


/*
  Submits a new MAC address.
*/
macreg.submit = function () {
  var macAddress = document.getElementById('macAddress').value;
  var description = document.getElementById('description').value
  var payload = {'macAddress': macAddress, 'description': description};
  var header = ['Content-Type', 'application/json'];
  var data = JSON.stringify(payload);
  return macreg.makeRequest('POST', macreg.SUBMIT_URL + macreg.getQueryArgs(), data, header).then(
    macreg.render,
    function (error) {
      console.log('Could not submit MAC address:\n' + JSON.stringify(error));
      alert('Could not submit MAC address.');
    }
  );
};
