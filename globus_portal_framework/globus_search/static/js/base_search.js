

function basicSearch() {
    var loc = document.getElementById("nav-search-box").value;
    window.location.replace("/search?q=" + encodeURIComponent(loc.trim()));
}
