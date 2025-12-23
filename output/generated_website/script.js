document.addEventListener('DOMContentLoaded', function() {
    const yearSpan = document.getElementById('year');
    if (yearSpan) {
        yearSpan.textContent = new Date().getFullYear();
    }
});

// The Navbar toggle script was already embedded in index.html for simplicity,
// but for larger projects, it would also be here.
// document.getElementById('nav-toggle').onclick = function() {
//     document.getElementById('nav-content').classList.toggle('hidden');
// };
