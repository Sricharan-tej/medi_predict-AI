// Global UI interactions and menu controls

document.addEventListener("DOMContentLoaded", function() {
    setupMobileMenu();
    setupFlashAutoDismiss();
});

// Setup Mobile Menu Drawer Toggle
function setupMobileMenu() {
    const menuToggle = document.getElementById("menuToggle");
    const mainNav = document.getElementById("mainNav");
    
    if (menuToggle && mainNav) {
        menuToggle.addEventListener("click", function() {
            mainNav.classList.toggle("mobile-active");
            const icon = menuToggle.querySelector("i");
            if (icon) {
                icon.classList.toggle("fa-bars");
                icon.classList.toggle("fa-xmark");
            }
        });
    }
}

// Close Flash Notification Alert
function closeFlash(id) {
    const el = document.getElementById(id);
    if (el) {
        el.style.transition = "opacity 0.4s ease-out, transform 0.4s ease-out";
        el.style.opacity = "0";
        el.style.transform = "translateY(-10px)";
        setTimeout(() => {
            el.remove();
        }, 400);
    }
}

// Auto-Dismiss Flash Alerts after 5 seconds
function setupFlashAutoDismiss() {
    const messages = document.querySelectorAll(".flash-message");
    messages.forEach((msg) => {
        setTimeout(() => {
            if (msg && msg.parentNode) {
                closeFlash(msg.id);
            }
        }, 5000);
    });
}
