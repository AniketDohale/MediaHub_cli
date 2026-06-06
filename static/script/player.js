const video = document.getElementById("player");
const videoId = video.dataset.videoId;
const speed = document.getElementById("speed");
const qualitySelect = document.getElementById("qualitySelect");
const subtitleBtn = document.getElementById("subtitle-btn");
const downloadBtn = document.getElementById("downloadBtn");
const bufferHealth = document.getElementById("buffer-health");
const networkStatus = document.getElementById("network-status");

// Initial Style for Buffer and Network
if (bufferHealth && networkStatus) {
    bufferHealth.textContent = "--";
    networkStatus.textContent = "Loading";

    bufferHealth.style.color = "#ddd";
    networkStatus.style.color = "#ddd";
}

speed.addEventListener("change", function () {
    video.playbackRate = parseFloat(this.value);
});

if (qualitySelect) {
    qualitySelect.value = qualitySelect.dataset.defaultQuality;
    downloadBtn.href = `/media/download/${videoId}?quality=${qualitySelect.value}`;
    qualitySelect.addEventListener("change", async () => {
        const quality = qualitySelect.value;
        const currentTime = video.currentTime;
        const wasPlaying = !video.paused;

        video.pause();

        downloadBtn.href = `/media/download/${videoId}?quality=${quality}`;
        video.src = `/media/stream/${videoId}?quality=${quality}`;
        
        const onLoaded = () => {    
            video.currentTime = currentTime;

            if (wasPlaying) {
                video.play();
            }

            video.removeEventListener("loadedmetadata", restore);
        };
        video.addEventListener("loadedmetadata", onLoaded);
        video.load();

        const response = await fetch(`/media/metadata/${videoId}?quality=${quality}`);
        const metadata = await response.json();

        document.getElementById("resolution").textContent = metadata.resolution;
        document.getElementById("size").textContent = metadata.size_mb + " MB";
        document.getElementById("duration").textContent = metadata.duration;
        document.getElementById("bitrate").textContent = metadata.bitrate_mbps + " Mbps";
    });
}

if (subtitleBtn && video.textTracks.length > 0) {
    const track = video.textTracks[0];

    track.mode = "hidden";
    subtitleBtn.classList.remove("active");

    subtitleBtn.addEventListener("click", (e) => {
        e.preventDefault();
        const enabled = track.mode === "showing";
        track.mode = enabled ? "hidden" : "showing";
        subtitleBtn.classList.toggle("active", !enabled);
    });
}

setInterval(() => {
    if (video.ended)
        return;

    if (video.buffered.length === 0) {
        bufferHealth.textContent = "--";
        networkStatus.textContent = "Loading";

        bufferHealth.style.color = "#ddd";
        networkStatus.style.color = "#ddd";
        return;
    }

    const buffer = video.buffered.end(video.buffered.length - 1) - video.currentTime;

    bufferHealth.textContent = `${buffer.toFixed(1)} sec`; 

    if (buffer > 20) {
        bufferHealth.style.color = "#4CAF50";
        networkStatus.textContent = "Excellent";
        networkStatus.style.color = "#4CAF50";
    } else if (buffer > 10) {
        bufferHealth.style.color = "#8BC34A";
        networkStatus.textContent = "Good";
        networkStatus.style.color = "#8BC34A";
    } else if (buffer > 5) {
        bufferHealth.style.color = "#FFC107";
        networkStatus.textContent = "Fair";
        networkStatus.style.color = "#FFC107";
    } else {
        bufferHealth.style.color = "#F44336";
        networkStatus.textContent = "Poor";
        networkStatus.style.color = "#F44336";
    }
}, 1000);