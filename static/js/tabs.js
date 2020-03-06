
function display(evt, identifier, content, tab)
{
    // Declare all variables
    var i, tabcontents, tablinks;

    // Get all elements with class=content and hide them
    tabcontents = document.getElementsByClassName(content);
    for (i = 0; i < tabcontents.length; i++) {
        tabcontents[i].style.display = "none";
    }

    // Get all elements with class=tab and remove the class "active".
    tablinks = document.getElementsByClassName(tab);
    for (i = 0; i < tablinks.length; i++) {
        tablinks[i].className = tablinks[i].className.replace(" active", "");
    }

    // Show the current tab, and add an "active" class to the button that opened
    // the tab.
    document.getElementById(identifier).style.display = "block";
    evt.currentTarget.className += " active";
}
