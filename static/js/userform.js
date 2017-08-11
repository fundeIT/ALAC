var filesToSend = [];
var processing = false;

function main() {
    document.getElementById('file').onchange = pushFiles;
    document.getElementById('anonymous').onclick = toggleAnonymous;
    document.getElementById('send').onclick = prepareForm;

    var data = {};
    data.ticket = document.getElementById('ticket').value;
    if (data.ticket != '0') {
        data.year = document.getElementById('year').value;
        data.ticket_id = document.getElementById('ticket_id').value;
        data.email = document.getElementById('email').value;
        getThreads(data);
    }
}

function pushFiles() {
    var file = document.getElementById('file');
    var fileList = document.getElementById('filelist');
    filesToSend.push(file.files);
    fileList.innerHTML = "";
    for (var i = 0; i < filesToSend.length; i++) {
        files = filesToSend[i];
        for (var j = 0; j < files.length; j++) {
            li = document.createElement('li');
            li.innerHTML = files[j].name;
            fileList.appendChild(li);
        }
    }
}

function toggleAnonymous() {
    var email = document.getElementById('email');
    email.disabled =
        document.getElementById('anonymous').checked;
    if (!email.disable)
        email.focus();
}

function validateFields() {
    var valid = true;
    var msg = document.getElementById('msg')
    var msgAlert = document.getElementById('msgalert');
    if (msg.value == "") {
        msgAlert.innerHTML = "* Debe agregar información en este campo";
        valid = false;
        msg.focus();
    }
    else
        msgAlert.innerHTML = "";
    return valid;
}

function prepareForm() {
    var valid = validateFields();
    if (!valid)
        return false;
    data = {};
    data.year = document.getElementById('year').value;
    data.ticket = document.getElementById('ticket').value;
    data.ticket_id = document.getElementById('ticket_id').value;
    data.msg = document.getElementById('msg').value;
    data.email = document.getElementById('email').value;
    makeRequest(data);
}

function makeRequest(data) {
    if (processing) return;
    var http = new XMLHttpRequest();
    document.getElementById("Processing").innerHTML = "Procesando. Espere..."
    processing = true;
    http.onreadystatechange = function () {
        try {
            if (http.readyState === XMLHttpRequest.DONE) {
                if (http.status === 200) {
                   data = JSON.parse(http.response);
                   uploadFiles(data);
                   getThreads(data);
                }
                else
                    console.log('makeRequest: There was a problem with data');
                document.getElementById("Processing").innerHTML = ""
                processing = false;
            }
        }
        catch (e) {
            console.log(e.description);
        }
    }
    http.open('POST', '/ticket/new');
    http.setRequestHeader('Content-Type', 'application/json');
    http.send(JSON.stringify(data));
}

function uploadFiles(identifier) {
    var counter = 0;
    for (var i = 0; i < filesToSend.length; i++) {
        files = filesToSend[i];
        for (var j = 0; j < files.length || counter < 5; j++) {
            var form = new FormData();
            form.append('ticket', identifier.ticket);
            form.append('ticket_id', identifier.ticket_id);
            form.append('email', identifier.email)
            form.append('year', identifier.year);
            form.append('thread_id', identifier.thread_id)
            form.append('file', files[j]);

            var http = new XMLHttpRequest();
            http.onreadystatechange = function () {
                try {
                    if (http.readyState === XMLHttpRequest.DONE) {
                        if (http.status === 200)
                            getThreads(http.responseText);
                        else
                            console.log('There was a problem with data');
                        delete files[j];
                    }
                }
                catch (e) {
                    console.log(e.description);
                }
            }
            http.open('POST', '/attachment/upload');
            http.send(form);
            counter++;
            delete filesToSend[i];
        }
    }
}

function getThreads(data) {
    document.getElementById('year').value = data.year;
    document.getElementById('ticket').value = data.ticket;
    document.getElementById('ticket_id').value = data.ticket_id;
    document.getElementById('email').value = data.email;
    document.getElementById('file').value = null
    document.getElementById('filelist').innerHTML = ''
    msg = document.getElementById('msg')
    msg.value = "";
    msg.focus();

    document.getElementById('request').style.display = 'none';
    if (data.email != '')
        document.getElementById('contact').style.display = 'none';

    var form = new FormData();
    form.append('year', data.year);
    form.append('ticket', data.ticket);
    form.append('email', data.email);
    var http = new XMLHttpRequest();
    http.onreadystatechange = function () {
        try {
            if (http.readyState === XMLHttpRequest.DONE) {
                if (http.status === 200)
                    updateThreads(http.responseText)
                else
                    console.log('There was a problem with data')
            }
        }
        catch (e) {
            console.log(e.description);
        }
    }
    http.open('POST', '/threads');
    http.send(form);
}

function updateThreads(data) {
    prev = document.getElementById('previous')
    prev.innerHTML = data
}

window.onload = main;
