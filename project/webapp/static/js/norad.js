function redirect(slug) {
    window.location.href = slug;
}

function refreshPage() {
    window.location.reload();
}

function setRefreshDelay(time) {
    time = parseInt(time, 10);
    console.log("Nouveau délai de rafraîchissement : "+time/1000+"s");
    setTimeout(function(){
        refreshPage();
    },time);
}

function getCookieValue(cName) {
    const name = cName + "=";
    const cDecoded = decodeURIComponent(document.cookie);
    const cArr = cDecoded.split('; ');
    let res;
    cArr.forEach(val => {
        if (val.indexOf(name) === 0) res = val.substring(name.length);
    })

    return res;
}

function setTimerCookie(value) {
    value = parseInt(value, 10);
    document.cookie = "timer_token=" + value + "";
    setRefreshDelay(value);
    refresh_value.textContent = value/1000 + "s";
}

function moreDrops() {
    var dots = document.getElementById("dots-drops");
    var plusText = document.getElementById("plus-drops");
    var btn = document.getElementById("drops-button");
    var baseText = document.getElementById("last-drop");

    if (dots.style.display === "none") {
        dots.style.display = "inline";
        btn.innerHTML = "Voir plus";
        plusText.style.display = "none";
        baseText.style.display = "inline";
    } else {
        dots.style.display = "none";
        btn.innerHTML = "Voir moins";
        plusText.style.display = "inline";
        baseText.style.display = "none";
    }
}

// Affichage des 3 éléments dans le dashboard
function show_element(element_class) {
    var need_to_show = document.querySelectorAll(element_class);
    need_to_show.forEach(ele => {
        ele.style.display = "table-row";
    });
}

function hide_element(element_class) {
    var need_to_show = document.querySelectorAll(element_class);
    need_to_show.forEach(ele => {
        ele.style.display = "none";
    });
}