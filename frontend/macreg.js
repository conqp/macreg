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

        for (let header of headers) {
            xhr.setRequestHeader(...header);
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
    Creates a toggle button for the respective record.
*/
macreg._toggleButton = function (record) {
    const column = document.createElement('td');
    const buttonToggle = document.createElement('button');
    buttonToggle.setAttribute('data-id', record.id);

    if (record.ipv4address == null) {
        buttonToggle.setAttribute('class', 'btn btn-success macreg-toggle');
        buttonToggle.textContent = 'Enable';
    } else {
        buttonToggle.setAttribute('class', 'btn btn-warning macreg-toggle');
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
    buttonDelete.setAttribute('class', 'btn btn-danger macreg-delete');
    buttonDelete.setAttribute('data-id', record.id);
    buttonDelete.setAttribute('data-toggle', 'tooltip');
    buttonDelete.setAttribute('data-placement', 'top');
    buttonDelete.setAttribute('title', 'Delete this MAC address.');
    buttonDelete.textContent = 'Delete';
    column.appendChild(buttonDelete);
    return column;
};


/*
  Renders the respective records.
*/
macreg._render = function (response) {
    console.log('Rendering records.');
    const container = document.getElementById('records');
    container.innerHTML = '';

    for (let record of response.response) {
        let row = document.createElement('tr');
        let fields = [
            record.timestamp,
            record.userName,
            record.macAddress,
            record.description,
            record.ipv4address || 'N/A'
        ];

        for (let field of fields) {
            let column = document.createElement('td');
            column.textContent = field;
            row.appendChild(column)
        }

        row.appendChild(macreg._toggleButton(record));
        row.appendChild(macreg._deleteButton(record));
        container.appendChild(row);
    }

    for (let button of document.getElementsByClassName('macreg-toggle')) {
        button.addEventListener('click', function() {
            macreg._toggle(button.getAttribute('data-id'));
        });
    }

    for (let button of document.getElementsByClassName('macreg-delete')) {
        button.addEventListener('click', function() {
            macreg._delete(button.getAttribute('data-id'));
        });
    }
};


/*
  Toggles a MAC address between enabled / disabled.
*/
macreg._toggle = function (id) {
    return macreg.makeRequest('PATCH', macreg.SUBMIT_URL + '/' + id).then(
        macreg.render,
        function (error) {
            console.log('Could not toggle MAC address:\n' + JSON.stringify(error));
            alert(error.response);

            if (error.status == 401) {
                window.location = 'index.html';
            }
        }
    );
};


/*
    Deletes a MAC address.
*/
macreg._delete = function (id) {
    return macreg.makeRequest('DELETE', macreg.SUBMIT_URL + '/' + id).then(
        macreg.render,
        function (error) {
            console.log('Could not toggle MAC address:\n' + JSON.stringify(error));
            alert(error.response);

            if (error.status == 401) {
                window.location = 'index.html';
            }
        }
    );
};



/*
  Runs on submit.html.
*/
macreg.submitInit = function () {
    document.removeEventListener('DOMContentLoaded', macreg.submitInit);
    document.getElementById('btnSubmit').addEventListener('click', function(event) {
        event.preventDefault();
    });
    return macreg.render();
};


/*
  Renders the page.
*/
macreg.render = function () {
    return macreg.makeRequest('GET', macreg.SUBMIT_URL).then(
        macreg._render,
        function (error) {
            console.log('Could not query MAC addresses:\n' + JSON.stringify(error));

            if (error.status == 401) {
                // Session expired.
                alert(error.response);
                window.location = 'index.html';
            }
        }
    );
};


/*
  Attempts an automatic login.
*/
macreg.autoLogin = function () {
    document.removeEventListener("DOMContentLoaded", macreg.autoLogin);
    document.getElementById('btnLogin').addEventListener('click', function(event) {
        event.preventDefault();
    });

    const header = ['Content-Type', 'application/json'];
    return macreg.makeRequest('PUT', macreg.LOGIN_URL, null, header).then(
        function (response) {
            console.log('Successfully refreshed session.');
            console.log('Redirectoing to submit page.');
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
    const userName = document.getElementById('userName').value;
    const password = document.getElementById('password').value;
    const header = ['Content-Type', 'application/json'];
    const payload = {'userName': userName, 'passwd': password};
    const data = JSON.stringify(payload);
    return macreg.makeRequest('POST', macreg.LOGIN_URL, data, header).then(
        function (response) {
            console.log('Successfully logged in.');
            console.log('Redirecting to submit page.');
            window.location = 'submit.html';
        },
        function (error) {
            console.log('Login failed:\n' + JSON.stringify(error));
            alert(error.response || 'Anmeldung fehlgeschlagen.');
        }
    );
};


/*
  Submits a new MAC address.
*/
macreg.submit = function () {
    const macAddress = document.getElementById('macAddress').value;
    const description = document.getElementById('description').value
    const payload = {'macAddress': macAddress, 'description': description};
    const header = ['Content-Type', 'application/json'];
    const data = JSON.stringify(payload);
    return macreg.makeRequest('POST', macreg.SUBMIT_URL, data, header).then(
        function(response) {
            const form = document.getElementById('submitForm');
            form.reset();
            macreg.render();
        },
        function (error) {
            console.log('Could not submit MAC address:\n' + JSON.stringify(error));
            alert(error.response);

            switch(error.status) {
            case 401:
                window.location = 'index.html';
                break;
            default:
                macreg.render();
                break;
            }
        }
    );
};
