const video = document.getElementById("player");
const videoId = video.dataset.videoId;
const speed = document.getElementById("speed");
const qualitySelect = document.getElementById("qualitySelect");
const subtitleBtn = document.getElementById("subtitle-btn");
const downloadBtn = document.getElementById("downloadBtn");
const bufferHealth = document.getElementById("buffer-health");
const networkStatus = document.getElementById("network-status");

const castBtn = document.getElementById("cast-btn");
const deviceSelect = document.getElementById("deviceSelect");
const confirmCastBtn = document.getElementById("confirmCastBtn");
const castStatus = document.getElementById("cast-status");
const castDeviceName = document.getElementById("cast-device-name");
const cancelCastBtn = document.getElementById("cancelCastBtn");

let isCasting = localStorage.getItem("isCasting") === "true";
let activeDevice = localStorage.getItem("activeDevice") || null;

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

            video.removeEventListener("loadedmetadata", onLoaded);
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

document.addEventListener("DOMContentLoaded", function () {
    const btn = document.getElementById("videoSettingsBtn");

    if (btn) {
        btn.addEventListener("click", openVideoSettingsModal);
    }
});

window.openVideoSettingsModal = function () {
    const modal = document.getElementById("videoSettingsModal");
    if (!modal) return;

    modal.style.display = "flex";
    document.body.style.overflow = "hidden";
};

window.closeVideoSettingsModal = function () {
    const modal = document.getElementById("videoSettingsModal");
    if (!modal) return;

    modal.style.display = "none";
    document.body.style.overflow = "";
};

window.addEventListener("click", function (e) {
    document.querySelectorAll(".modal").forEach(modal => {
        if (e.target === modal) {
            modal.style.display = "none";
            document.body.style.overflow = "";
        }
    });
});

// Casting To TV
async function loadDevices() {
    deviceSelect.innerHTML = "<option>Searching...</option>";

    const res = await fetch("/cast/devices");
    const devices = await res.json();

    deviceSelect.innerHTML = "";

    if (devices.length === 0) {
        deviceSelect.innerHTML = "<option>No Devices Found</option>";
        return;
    }

    devices.forEach(device => {
        const option = document.createElement("option");
        option.value = device.udn;
        option.textContent = device.name;

        deviceSelect.appendChild(option);
    });
}

castBtn.addEventListener("click", async () => {
    if (isCasting) {
        stopCasting();
        return;
    }

    await loadDevices();
    document.getElementById("castModal").style.display = "flex";
});

if (castBtn) {
    const icon = castBtn.querySelector("img");
    confirmCastBtn.addEventListener("click", async () => {
        const udn = deviceSelect.value;

        const quality = qualitySelect ? qualitySelect.value : "";

        let url = `/cast-start/${videoId}?udn=${encodeURIComponent(udn)}`;
        if (quality) {
            url += `&quality=${quality}`;
        }

        const res = await fetch(url, {
            method: "POST"
        });

        if (!res.ok) {
            alert("Casting Failed");
            return;
        }

        const result = await res.json();

        isCasting = true;
        activeDevice = result.udn;

        localStorage.setItem("isCasting", "true");
        localStorage.setItem("activeDevice", result.udn);
        localStorage.setItem("activeDeviceName", result.tv);

        showCastingStatus(result.tv);

        castBtn.querySelector("img").src = "/static/icons/stop-cast.png";
        castBtn.classList.add("active");
        document.getElementById("castModal").style.display = "none";
    });
}

async function stopCasting() {
    const res = await fetch("/cast-stop", {
        method: "POST",

        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            udn: activeDevice
        })
    });

    if (!res.ok)
        return;

    isCasting = false;
    activeDevice = null;

    localStorage.removeItem("isCasting");
    localStorage.removeItem("activeDevice");
    localStorage.removeItem("activeDeviceName");

    hideCastingStatus();

    castBtn.querySelector("img").src = "/static/icons/cast.png";
    castBtn.classList.remove("active");
}

cancelCastBtn.addEventListener("click", () => {
    document.getElementById("castModal").style.display = "none";
});

function showCastingStatus(deviceName) {
    castDeviceName.textContent = deviceName;
    castStatus.style.display = "inline";
}

function hideCastingStatus() {
    castStatus.style.display = "none";
    castDeviceName.textContent = "";
}

document.addEventListener("DOMContentLoaded", () => {
    if (localStorage.getItem("isCasting") === "true") {

        const deviceName = localStorage.getItem("activeDeviceName");
        if (deviceName) {
            showCastingStatus(deviceName);
            castBtn.querySelector("img").src = "/static/icons/stop-cast.png";
            castBtn.classList.add("active");
        }
    }
});