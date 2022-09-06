window.onload = function() {
    // find all elements with class 'active', and remove the 'active' class, USE VANILLA JS
    var active = document.getElementsByClassName("active");
    for (var i = 0; i < active.length; i++) {
        active[i].classList.remove("active");
    }
    // add a active class to the element with the id of link-about
    document.getElementById("link-organizations").classList.add("active");
}

