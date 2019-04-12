/*
    (C) 2018-2019 Richard Neumann <mail at richard dash neumann period de>

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

const macreg = {};

macreg.LOGIN_URL = 'login';
macreg.SUBMIT_URL = 'mac';


/*
  Makes a request returning a promise.
*/
macreg.makeRequest = function (method, url, data = null, headers = {}) {
    function parseResponse (response) {
        try {
            return JSON.parse(response);
        } catch (error) {
            return response;
        }
    }

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
        }

        function onerror () {
            reject({
                response: parseResponse(xhr.response),
                status: this.status,
                statusText: xhr.statusText
            });
        }

        const xhr = new XMLHttpRequest();
        xhr.withCredentials = true;
        xhr.open(method, url);

        for (const header in headers) {
            xhr.setRequestHeader(header, headers[header]);
        }

        xhr.onload = onload;
        xhr.onerror = onerror;

        if (data == null) {
            xhr.send();
        } else {
            xhr.send(data);
        }
    }

    return new Promise(executor);
};


/*
    Filters MAC address records.
*/
macreg._filter = function* (records) {
    const filterString = document.getElementById('filter').value.trim();

    if (filterString == '') {
        yield* records;
        return;
    }

    for (const record of records) {
        let matchDate = record.timestamp.includes(filterString);
        let matchUserName = record.userName.includes(filterString);
        let matchMacAddress = record.macAddress.includes(filterString);
        let matchDescription = record.description.includes(filterString);
        let matchIpv4address = record.ipv4address.includes(filterString);

        if (matchDate || matchUserName || matchMacAddress || matchDescription || matchIpv4address) {
            yield record;
        }
    }
};


/*
    Creates a toggle button for the respective record.
*/
macreg._toggleButton = function (record) {
    const column = document.createElement('td');
    const buttonToggle = document.createElement('button');
    buttonToggle.setAttribute('data-id', record.id);

    if (record.ipv4address == null) {
        buttonToggle.setAttribute('class', 'w3-button w3-green macreg-toggle');
        buttonToggle.textContent = 'Enable';
    } else {
        buttonToggle.setAttribute('class', 'w3-button w3-orange macreg-toggle');
        buttonToggle.textContent = 'Disable';
    }

    column.appendChild(buttonToggle);
    return column;
};


/*
    Creates a delete button for the respective record.
*/
macreg._deleteButton = function (record) {
    const column = document.createElement('td');
    const buttonDelete = document.createElement('button');
    buttonDelete.setAttribute('class', 'w3-button w3-red macreg-delete');
    buttonDelete.setAttribute('data-id', record.id);
    buttonDelete.textContent = 'Delete';
    column.appendChild(buttonDelete);
    return column;
};


/*
  Renders the respective records.
*/
macreg._render = function (response) {
    const container = document.getElementById('records');
    container.innerHTML = '';
    const records = macreg._filter(response.response);

    for (const record of records) {
        let row = document.createElement('tr');
        let fields = [
            record.timestamp,
            record.userName,
            record.macAddress,
            record.description,
            record.ipv4address || 'N/A'
        ];

        for (const field of fields) {
            let column = document.createElement('td');
            column.textContent = field;
            row.appendChild(column);
        }

        row.appendChild(macreg._toggleButton(record));
        row.appendChild(macreg._deleteButton(record));
        container.appendChild(row);
    }

    for (const button of document.getElementsByClassName('macreg-toggle')) {
        button.addEventListener('click', function() {
            macreg._toggle(button.getAttribute('data-id'));
        });
    }

    for (const button of document.getElementsByClassName('macreg-delete')) {
        button.addEventListener('click', function() {
            macreg._delete(button.getAttribute('data-id'));
        });
    }
};


/*
    Handles common request errors.
*/
macreg._handleError = function (error) {
    alert(error.response);

    if (error.status == 401) {  // Session expired.
        window.location = 'index.html';
    }
};


/*
  Toggles a MAC address between enabled / disabled.
*/
macreg._toggle = function (id) {
    return macreg.makeRequest('PATCH', macreg.SUBMIT_URL + '/' + id).then(macreg.render, macreg._handleError);
};


/*
    Deletes a MAC address.
*/
macreg._delete = function (id) {
    return macreg.makeRequest('DELETE', macreg.SUBMIT_URL + '/' + id).then(macreg.render, macreg._handleError);
};


/*
  Initializes the login page.
*/
macreg.loginInit = function () {
    document.removeEventListener('DOMContentLoaded', macreg.loginInit);
    document.getElementById('btnLogin').addEventListener('click', function(event) {
        event.preventDefault();
        macreg.login();
    });
};


/*
  Initializes the submit page.
*/
macreg.submitInit = function () {
    document.removeEventListener('DOMContentLoaded', macreg.submitInit);
    document.getElementById('btnSubmit').addEventListener('click', function(event) {
        event.preventDefault();
        macreg.submit();
    });
    document.getElementById('filter').addEventListener('change', macreg.render);
    return macreg.render();
};


/*
  Renders the page.
*/
macreg.render = function () {
    return macreg.makeRequest('GET', macreg.SUBMIT_URL).then(macreg._render, macreg._handleError);
};


/*
  Performs a login.
*/
macreg.login = function () {
    const userName = document.getElementById('userName').value;
    const password = document.getElementById('password').value;
    const headers = {'Content-Type': 'application/json'};
    const payload = {'userName': userName, 'passwd': password};
    const data = JSON.stringify(payload);
    return macreg.makeRequest('POST', macreg.LOGIN_URL, data, headers).then(
        function () {
            window.location = 'submit.html';
        },
        function (error) {
            alert(error.response || 'Login failed.');
        }
    );
};


/*
  Submits a new MAC address.
*/
macreg.submit = function () {
    const macAddress = document.getElementById('macAddress').value;
    const description = document.getElementById('description').value;
    const payload = {'macAddress': macAddress.trim(), 'description': description.trim()};
    const headers = {'Content-Type': 'application/json'};
    const data = JSON.stringify(payload);
    return macreg.makeRequest('POST', macreg.SUBMIT_URL, data, headers).then(
        function () {
            document.getElementById('submitForm').reset();
            macreg.render();
        },
        function (error) {
            alert(error.response);

            if (error.status == 401) {
                window.location = 'index.html';
            } else {
                macreg.render();
            }
        }
    );
};
