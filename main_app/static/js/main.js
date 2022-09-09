// $(function() {
//     // this will get the full URL at the address bar
//     var url = window.location.href;
//
//     // passes on every "a" tag
//     $(".navbar-nav li").each(function() {
//         // checks if its the same on the address bar
//         if (url == (this.href)) {
//             $(this).closest("li").addClass("active");
//             //for making parent of submenu active
//            $(this).closest("li").parent().parent().addClass("active");
//         }
//     });
// });
//

window.onload = function () {
  let url = '';
  if (window.location) {
    url = window.location.href;
  }
  //    loop through all the '.navbar-nav li' elements use for each loop with VANILLA JS
  const navItems = document
    .getElementsByClassName('navbar-nav')[0]
    .getElementsByTagName('li');
  // loop through navItems, check if the url is the same as the href of the nav item
  for (var i = 0; i < navItems.length; i++) {
    if (
      navItems[i].getElementsByTagName('a')[0] &&
      url == navItems[i].getElementsByTagName('a')[0].href
    ) {
      navItems[i].classList.add('active');
      // for making parent of submenu active
      navItems[i].parentElement.parentElement.classList.add('active');
    }
  }
};
