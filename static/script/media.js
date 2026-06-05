const searchInput = document.getElementById("videoSearch");
const buttons = document.querySelectorAll(".cat-btn");
const videoCount = document.getElementById("videoCount");

let activeCategory = "All";

function filterVideos() {
    const search = searchInput.value.toLowerCase();
    let visibleCount = 0;

    document.querySelectorAll(".video-card").forEach(card => {
        const textMatch = card.textContent.toLowerCase().includes(search);
        const category = card.dataset.category;
        const categoryMatch = activeCategory === "All" || category === activeCategory;
        const visible = textMatch && categoryMatch;
        
        card.style.display = (textMatch && categoryMatch) ? "" : "none";
        if (visible) {
            visibleCount++;
        }
    });
    videoCount.textContent = `${visibleCount} Video${visibleCount !== 1 ? "s" : ""}`;
}

searchInput?.addEventListener("input", filterVideos);

buttons.forEach(btn => {
    btn.addEventListener("click", () => {

        buttons.forEach(b => b.classList.remove("active"));
        btn.classList.add("active");

        activeCategory = btn.dataset.category;
        filterVideos();
    });
});
filterVideos();