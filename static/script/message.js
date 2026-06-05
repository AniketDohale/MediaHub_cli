document.addEventListener("DOMContentLoaded", () => {
    const msg = document.getElementById("flash-msg");

    if (!msg) return;

    setTimeout(() => {
        msg.classList.add("hide");

        setTimeout(() => msg.remove(), 450);
    }, 3000);
});