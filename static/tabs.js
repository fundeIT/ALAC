function openTab(evt, tabName) {
    var i, tabcontent, tablinks;
    tabcontent = document.getElementsByClassName("tabcontent");
    for (i = 0; i < tabcontent.length; i++) {
        tabcontent[i].style.display = "none";
    }
    tablinks = document.getElementsByClassName("tablinks");
    for (i = 0; i < tablinks.length; i++) {
        tablinks[i].className = tablinks[i].className.replace(" active", "");
    }
    if (tabName) {
        document.getElementById(tabName).style.display = "block";
        evt.currentTarget.className += " active";
    }
    else {
        tabcontent = document.getElementsByClassName("tabcontent");
        tabcontent[0].style.display = "block";
        tablinks = document.getElementsByClassName("tablinks");
        tablinks[0].className = tablinks[0].className += " active";
    }
}

window.onload = function() {
    openTab(null, null);
}
