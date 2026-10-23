// kodx.uz — umumiy skriptlar: mavzu almashtirish, mobil menyu, KaTeX formulalari
(function () {
  "use strict";

  document.querySelectorAll("[data-theme-toggle]").forEach(function (button) {
    button.addEventListener("click", function () {
      var dark = document.documentElement.classList.toggle("dark");
      try { localStorage.setItem("kodx-theme", dark ? "dark" : "light"); } catch (e) {}
    });
  });

  var toggle = document.querySelector("[data-menu-toggle]");
  var menu = document.querySelector("[data-menu]");
  if (toggle && menu) {
    toggle.addEventListener("click", function () {
      var open = menu.classList.toggle("hidden") === false;
      menu.classList.toggle("flex", open);
      toggle.setAttribute("aria-expanded", String(open));
    });
  }

  // data-confirm — yuborishdan oldin tasdiq; data-autosubmit — tanlov o'zgarganda formani yuborish
  document.addEventListener("submit", function (event) {
    var message = event.target.getAttribute("data-confirm");
    if (message && !window.confirm(message)) event.preventDefault();
  });
  document.addEventListener("change", function (event) {
    if (event.target.hasAttribute("data-autosubmit") && event.target.form) event.target.form.submit();
  });

  // .math elementlaridagi $...$ formulalarni KaTeX bilan chizish (KaTeX yuklangan sahifalarda)
  window.kodxRenderMath = function (root) {
    if (!window.katex) return;
    (root || document).querySelectorAll(".math").forEach(function (el) {
      var src = el.textContent.trim();
      var display = src.startsWith("$$");
      var body = src.replace(/^\$\$?|\$\$?$/g, "");
      try { window.katex.render(body, el, { displayMode: display, throwOnError: false }); } catch (e) {}
    });
  };
})();
