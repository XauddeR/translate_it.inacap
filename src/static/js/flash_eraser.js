document.addEventListener("DOMContentLoaded", () => {
    const flashMessages = document.querySelectorAll(".containerFlashMessage");

    if (!flashMessages.length) return;

    setTimeout(() => {
        flashMessages.forEach(el => {
            el.style.transition = "opacity 0.6s ease, transform 0.6s ease";
            el.style.opacity = "0";
            el.style.transform = "translateY(-6px)";

            setTimeout(() => el.remove(), 600);
        });
    }, 5000);
});