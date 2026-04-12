document.addEventListener("DOMContentLoaded", () => {
    const toggleButton = document.querySelector(".nav-toggle");
    const nav = document.querySelector(".main-nav");
    const passwordToggles = document.querySelectorAll(".password-toggle");

    if (toggleButton && nav) {
        toggleButton.addEventListener("click", () => {
            nav.classList.toggle("open");
        });
    }

    passwordToggles.forEach((toggle) => {
        const targetId = toggle.getAttribute("data-target");
        const input = targetId ? document.getElementById(targetId) : null;

        if (!input) {
            return;
        }

        toggle.addEventListener("click", () => {
            const isPassword = input.type === "password";
            const showText = toggle.getAttribute("data-show-text") || "Show";
            const hideText = toggle.getAttribute("data-hide-text") || "Hide";
            const showLabel = toggle.getAttribute("data-show-label") || "Show password";
            const hideLabel = toggle.getAttribute("data-hide-label") || "Hide password";
            input.type = isPassword ? "text" : "password";
            toggle.textContent = isPassword ? hideText : showText;
            toggle.setAttribute("aria-label", isPassword ? hideLabel : showLabel);
        });
    });
});
