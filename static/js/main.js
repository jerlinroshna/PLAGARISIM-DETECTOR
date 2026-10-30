// CodeGuard Academic Portal - Master Script Coordinator
// Dynamically loads modularized functional components
(function () {
  const currentScript = document.currentScript;
  let basePath = "/static/js";
  if (currentScript && currentScript.src) {
    basePath = currentScript.src.substring(0, currentScript.src.lastIndexOf("/"));
  }

  const modules = [
    "core.js",
    "editor.js",
    "student.js",
    "faculty.js",
    "assignments.js"
  ];

  modules.forEach(function (modName) {
    const script = document.createElement("script");
    script.src = basePath + "/modules/" + modName + "?v=4.0";
    script.defer = true;
    document.head.appendChild(script);
  });
})();
