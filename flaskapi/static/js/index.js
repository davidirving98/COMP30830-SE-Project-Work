// Global array for storing the station data from the API
let stations = [];

// Initialise route mapping variables
let selectedStart = null;
let selectedEnd = null;
let currentStation = null;
let activeRenderers = [];
let clickMarkers = [];
let routeMarkers = [];
let startMarker = null;
let endMarker = null;

// reverse geocoding from Google Maps
let geocoder;

// Load Google Charts once to speed up
google.charts.load('current', { packages: ['corechart'] });

function toLocalDatetimeValue(d) {
    const pad = (n) => String(n).padStart(2, "0");
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function initPredictControls() {
    const dtInput = document.getElementById("predict-datetime");
    const btn = document.getElementById("predict-btn");
    if (!dtInput || !btn) return;

    // Limit selectable time: now -> now + 7 days
    const now = new Date();
    const max = new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000);
    dtInput.min = toLocalDatetimeValue(now);
    dtInput.max = toLocalDatetimeValue(max);
    dtInput.value = dtInput.min;

    btn.addEventListener("click", predictByInput);
}

async function predictByInput() {
    const stationInput = document.getElementById("predict-station-id");
    const dtInput = document.getElementById("predict-datetime");
    const resultEl = document.getElementById("predict-result");
    if (!stationInput || !dtInput || !resultEl) return;

    const stationId = Number(stationInput.value);
    const dt = dtInput.value; // YYYY-MM-DDTHH:mm
    if (!stationId || !dt) {
        resultEl.innerText = "Please enter station number and datetime.";
        return;
    }

    // Convert datetime-local to backend format: YYYY-MM-DD HH:MM:SS
    const dtForApi = `${dt.replace("T", " ")}:00`;
    const url = `/predict/by-input?station_id=${encodeURIComponent(stationId)}&datetime=${encodeURIComponent(dtForApi)}`;

    resultEl.innerText = "Predicting...";
    try {
        const resp = await fetch(url);
        const data = await resp.json();
        if (!resp.ok) {
            resultEl.innerText = `Error: ${data.error || "request failed"}`;
            return;
        }

        const pred = Array.isArray(data.pred_available_bikes)
            ? data.pred_available_bikes[0]
            : data.pred_available_bikes;
        resultEl.innerText = `Predicted available bikes: ${pred}`;
    } catch (err) {
        resultEl.innerText = `Error: ${err.message}`;
    }
}

function addMarkers(stations) {
    console.log(stations);
    // Create a marker for each station
    for (const station of stations) {
        // Assign a colour to each marker based on availability
        const color = getStationColor(station);

        const icon = {
            url: `/static/icons/bike-${color}.svg`,
            scaledSize: new google.maps.Size(28, 28)
        };

        // Create the Google Maps marker
        const marker = new google.maps.Marker({
            position: {
                lat: Number(station.lat),
                lng: Number(station.lng),
            },
            map: map,
            title: station.name,
            station_number: station.number,
            icon: icon,
        });

        // Save marker reference for later searches
        station.marker = marker;

        // Show the info window upon click
        marker.addListener("click", () => {
            // Call routing function
            currentStation = station;
            
            openDrawer(station);
            
            // Info window content (html)
            const content = `
                <div>
                    <h3>${station.name}</h3>
                    <p><strong>Available Bikes:</strong> ${station.available_bikes || "N/A"}</p>
                    <p><strong style="color:#d4af37;">Free Stands:</strong> <span style="color:#d4af37;">${station.available_stands || "N/A"}</span></p>
                    <div id="chart_div_${station.number}" style="width: 320px; height: 220px;"></div>
                </div>
            `;

            // Set the content and open the window
            infoWindow.setContent(content);
            infoWindow.open(map, marker);

            // Draw a time-series chart (last 5 records) once the library is ready
            google.charts.setOnLoadCallback(async () => {
                const chartData = new google.visualization.DataTable();
                chartData.addColumn('datetime', 'Time');
                chartData.addColumn('number', 'Available Bikes');
                chartData.addColumn('number', 'Free Stands');

                let historyRows = [];
                try {
                    const response = await fetch(`/station/${station.number}/history`);
                    if (!response.ok) {
                        throw new Error(`history API failed: ${response.status}`);
                    }
                    const history = await response.json();
                    historyRows = history
                        .map((item) => {
                            // DB stores UTC naive datetime text, so append 'Z' to parse as UTC.
                            const ts = new Date(`${String(item.last_update).replace(" ", "T")}Z`);
                            if (!Number.isFinite(ts.getTime())) {
                                return null;
                            }
                            return [
                                ts,
                                Number(item.available_bikes ?? 0),
                                Number(item.available_bike_stands ?? 0),
                            ];
                        })
                        .filter(Boolean);
                } catch (err) {
                    console.error("Error fetching station history:", err);
                }

                if (historyRows.length === 0) {
                    historyRows = [[
                        new Date(),
                        Number(station.available_bikes ?? 0),
                        Number(station.available_stands ?? 0),
                    ]];
                }

                chartData.addRows(historyRows);

                const options = {
                    title: 'Station Time Series Overview',
                    legend: { position: 'bottom' },
                    curveType: 'function',
                    series: {
                        1: { color: '#d4af37' },
                    },
                    hAxis: {
                        title: 'Time',
                        format: 'HH:mm',
                    },
                    vAxis: {
                        title: 'Count',
                    },
                    width: 320,
                    height: 220,
                };

                // Draw the line chart
                const chart = new google.visualization.LineChart(
                    document.getElementById(`chart_div_${station.number}`)
                );

                chart.draw(chartData, options);
            });
        });
    }
}

function getStations() {
    // Send a request to the "/stations" endpoint in our flask function to retrieve station data
    fetch("/stations")
        .then((response) => {
            if (!response.ok) {
                throw new Error(`/stations failed: ${response.status}`);
            }
            return response.json();
        })
        .then((data) => {
            console.log("fetch response", typeof data);

            // Store stations globally and create map markers
            stations = data;
            addMarkers(stations);

            // Calculate summary stats for the bottom bar
            let totalBikes = data.reduce((sum, s) => sum + s.available_bikes, 0);

            let openStations = data.filter(
                s => s.available_bikes + s.available_stands > 0
            ).length;

            document.getElementById("bikes-available").innerText =
                totalBikes + " Bikes Available";

            document.getElementById("stations-open").innerText =
                openStations + " Stations Open";
        })
        .catch((error) => {
            console.error("Error fetching stations data:", error);
        });
}

// display current weather information
async function loadCurrentWeather() {
    try{
        const response = await fetch("/weather");
        const data = await response.json();

        const temp = Math.round(data.temperature)
        const windspeed = Math.round(data.wind_speed)
        document.getElementById("temperature").textContent = `${temp}°C`;
        document.getElementById("weather").textContent = data.weather;
        document.getElementById("wind_speed").textContent = `${windspeed}m/s`;
        document.getElementById("humidity").textContent = data.humidity + "%";
    } catch (error) {
        console.error("Weather load failed:", error);
    }
}

// display forecast weather information
async function loadForecast() {
    try {
        const response = await fetch("/forecast");
        const data = await response.json();

        // 1st forecast card
        const temp1 = Math.round(data[0].temperature);
        document.getElementById("forecast1-time").textContent = data[0].forecast_time;
        document.getElementById("forecast1-temp").textContent = `${temp1}°C`;
        document.getElementById("forecast1-desc").textContent = data[0].weather;
        document.getElementById("forecast1-humidity").textContent =  `💧 ${data[0].humidity}%`;

        // 2nd forecast card
        const temp2 = Math.round(data[1].temperature);
        document.getElementById("forecast2-time").textContent = data[1].forecast_time;
        document.getElementById("forecast2-temp").textContent = `${temp2}°C`;
        document.getElementById("forecast2-desc").textContent = data[1].weather;
        document.getElementById("forecast2-humidity").textContent =  `💧 ${data[0].humidity}%`;

    } catch (err) {
        console.error("Forecast load failed:", err);
    }
}

document.addEventListener("DOMContentLoaded", () => {
    loadCurrentWeather();
    loadForecast();
    initPredictControls();
});

// Initialize and add the map
    function initMap() {
        const dublin = { lat: 53.35014, lng: -6.266155 };
        
        geocoder = new google.maps.Geocoder();
        
        const dublinBounds = {
        north: 53.45,
        south: 53.25,
        west: -6.45,
        east: -6.05
        };

        map = new google.maps.Map(document.getElementById("map"), {
        zoom: 14,
        center: dublin,
        restriction: {
            latLngBounds: dublinBounds,
            strictBounds: true
        }
    });
        
    let clickStage = "start";

    map.addListener("click", (e) => {
    infoWindow.close();

    const clickedLocation = {
        lat: e.latLng.lat(),
        lng: e.latLng.lng()
    };

    const marker = new google.maps.Marker({
        position: clickedLocation,
        map: map
    });

    clickMarkers.push(marker);

    // Create model
    const isStart = clickStage === "start";

    const content = `
        <div class="map-popup">
            <div class="popup-text">
                ${isStart ? "Set as starting point?" : "Set as destination?"}
            </div>
            <div class="popup-actions">
                <button id="confirm-btn" class="btn primary">Yes</button>
                <button id="cancel-btn" class="btn secondary">No</button>
            </div>
        </div>
    `;

    infoWindow.setContent(content);
    infoWindow.open(map, marker);

    google.maps.event.addListenerOnce(infoWindow, 'domready', () => {
        document.getElementById("confirm-btn").addEventListener("click", () => {
            confirmPoint(
                isStart ? "start" : "end",
                clickedLocation.lat,
                clickedLocation.lng
            );
        });
        document.getElementById("cancel-btn").addEventListener("click", () => {
            cancelPoint();
        });
});
});

function confirmPoint(type, lat, lng) {
    const location = { lat, lng };

    if (type === "start") {
        selectedStart = location;

        // Delete original start marker
        if (startMarker) startMarker.setMap(null);

        // Create new start market
        startMarker = new google.maps.Marker({
            position: location,
            map: map,
            label: "A"
        });

        // Delete temporary marker
        clickMarkers.forEach(m => m.setMap(null));
        clickMarkers = [];

        document.getElementById("start-input").value =
            `${lat.toFixed(4)}, ${lng.toFixed(4)}`;

        // geocoder
        if (geocoder) {
            geocoder.geocode({ location }, (results, status) => {
                if (status === "OK" && results[0]) {
                    document.getElementById("start-input").value =
                        results[0].formatted_address;
                }
            });
        }

        document.getElementById("route-status").innerText =
            "Start selected — now choose destination";

        clickStage = "end";
        infoWindow.close();

    } else {
        selectedEnd = location;

        // Delete original end marker
        if (endMarker) endMarker.setMap(null);

        // Create new end marker
        endMarker = new google.maps.Marker({
            position: location,
            map: map,
            label: "D"
        });

        // Delete temporary marker
        clickMarkers.forEach(m => m.setMap(null));
        clickMarkers = [];

        document.getElementById("end-input").value =
            `${lat.toFixed(4)}, ${lng.toFixed(4)}`;

        if (geocoder) {
            geocoder.geocode({ location }, (results, status) => {
                if (status === "OK" && results[0]) {
                    document.getElementById("end-input").value =
                        results[0].formatted_address;
                }
            });
        }

        document.getElementById("route-status").innerText =
            "Route calculating...";

        clickStage = "start";

        infoWindow.close();

        // Draw the route
        calculateSmartRoute(selectedStart, selectedEnd);
    }
}

function cancelPoint() {
    clickMarkers.forEach(m => m.setMap(null));
    clickMarkers = [];
    infoWindow.close();
}

    // Single reusable information window
    infoWindow = new google.maps.InfoWindow();
    
    // Route Mapping
    directionsService = new google.maps.DirectionsService();

    // Load station data
    getStations();
    
    initAutocomplete();
}

function isWithinDublin(location) {
    return (
        location.lat >= 53.25 &&
        location.lat <= 53.45 &&
        location.lng >= -6.45 &&
        location.lng <= -6.05
    );
}

// Function to decide the marker colour
function getStationColor(station) {

    if (station.available_bikes === 0 && station.available_stands === 0) {
        return "grey";   // station closed / no data
    }
    if (station.available_bikes === 0) {
        return "red";    // no bikes
    }
    if (station.available_stands === 0) {
        return "green";  // station full
    }
    return "blue";       // bikes available
}

document.addEventListener("DOMContentLoaded", () => {
    const welcomeModal = document.getElementById("welcome-modal");
    const closeWelcome = document.getElementById("close-welcome");
    const startBtn = document.getElementById("start-btn");
    const howItWorksBtn = document.getElementById("how-it-works-btn");

    // Show modal when page first loads only
    if (!localStorage.getItem("wheelyWelcomeSeen")) {
        welcomeModal.style.display = "flex";
        localStorage.setItem("wheelyWelcomeSeen", true);
    }

    // Close modal
    function closeModal() {
        welcomeModal.style.display = "none";
    }

    // Open modal
    function openModal() {
        welcomeModal.style.display = "flex";
    }

    closeWelcome.addEventListener("click", closeModal);
    startBtn.addEventListener("click", closeModal);
    
    // Reopen modal when clicked
    if (howItWorksBtn) {
        howItWorksBtn.addEventListener("click", openModal);
    }
});


document.addEventListener("DOMContentLoaded", () => {

    const searchInput = document.getElementById("station-search");
    const resultsContainer = document.getElementById("search-results");

    // Listen for user typing in the search box
    searchInput.addEventListener("input", function () {

        const search = this.value.toLowerCase();

        // Clear previous results
        resultsContainer.innerHTML = "";

        // Hide the dropdown if search is empty
        if (search.length === 0) {
            resultsContainer.style.display = "none";
            return;
        }

        // Find matching stations by their name or number (in the json)
        const matches = stations.filter(station =>
            station.name.toLowerCase().includes(search) ||
            station.number.toString().includes(search)
        );

        // Show first 8 matches in the dropdown menu
        matches.slice(0, 8).forEach(station => {

            const item = document.createElement("div");
            item.className = "search-item";

            item.innerHTML = `
                <strong>${station.name}</strong><br>
                🚲 ${station.available_bikes} bikes available
            `;

            // Zoom to the matching marker upon click
            item.addEventListener("click", () => {

                map.panTo({
                    lat: Number(station.lat),
                    lng: Number(station.lng)
                });

                map.setZoom(16);

                // Trigger marker click to open info window
                google.maps.event.trigger(station.marker, "click");

                resultsContainer.style.display = "none";
                searchInput.value = station.name;
            });

            resultsContainer.appendChild(item);
        });

        // Show dropdown menu if matches exist
        resultsContainer.style.display = matches.length ? "block" : "none";
    });

    // Close dropdown when clicking elsewhere
    document.addEventListener("click", (e) => {
        if (!e.target.closest(".search-container")) {
            resultsContainer.style.display = "none";
        }
    });

});

// Routing Slide Drawer
function openDrawer(station = null) {
    const drawer = document.getElementById("drawer");
    if (!drawer) return;

    const title = document.getElementById("drawer-title");

    
    if (station) {
        currentStation = station;
    document.getElementById("drawer-title").innerText = station.name;
    const sid = document.getElementById("predict-station-id");
    if (sid) sid.value = station.number;

    } else {
    document.getElementById("drawer-title").innerText = "Route Planner";
    }
    
    drawer.classList.add("open");
}

function closeDrawer()  {
    document.getElementById("drawer").classList.remove("open");
}

// Routing Function
function calculateSmartRoute(start, end) {
    infoWindow.close();
    if (stations.length === 0) {
        alert("Stations still loading...");
        return;
    }
    
    if (!isWithinDublin(start) || !isWithinDublin(end)) {
    alert("Route must be within Dublin");
    return;
}
    
    clearRoute();
    document.getElementById("route-actions").style.display = "none";

    const startStation = getNearestStartStation(start);
    const endStation = getNearestEndStation(end);

    if (!startStation || !endStation) {
        alert("No nearby stations available");
        return;
    }

    const segments = [
        {
            origin: start,
            destination: {
                lat: Number(startStation.lat),
                lng: Number(startStation.lng)
            },
            mode: google.maps.TravelMode.WALKING,
            color: "#FFFF00", // yellow
            label: `A to B: 🚶 Walk to ${startStation.name}`
        },
        {
            origin: {
                lat: Number(startStation.lat),
                lng: Number(startStation.lng)
            },
            destination: {
                lat: Number(endStation.lat),
                lng: Number(endStation.lng)
            },
            mode: google.maps.TravelMode.BICYCLING,
            color: "#FF0000", // red
            label: `B to C: 🚲 Cycle to ${endStation.name}`
        },
        {
            origin: {
                lat: Number(endStation.lat),
                lng: Number(endStation.lng)
            },
            destination: end,
            mode: google.maps.TravelMode.WALKING,
            color: "#FFFF00",
            label: "C to D: 🚶 Walk to your destination"
        }
    ];

    drawSegments(segments);
}

function drawSegments(segments) {
    let totalDistance = 0;
    let totalDuration = 0;
    let completed = 0;

    let routePoints = [];
    let segmentResults = new Array(segments.length);

    // Clear old route markers first
    routeMarkers.forEach(m => m.setMap(null));
    routeMarkers = [];

    // Create A → B → C → D markers ONCE
    const points = [
        segments[0].origin,              // A
        segments[0].destination,         // B
        segments[1].destination,         // C
        segments[2].destination          // D
    ];

    const labels = ["A", "B", "C", "D"];

    points.forEach((point, i) => {
        const marker = new google.maps.Marker({
            position: point,
            map: map,
            label: labels[i]
        });
        routeMarkers.push(marker);
    });

    // Loop through segments (no markers inside here)
    segments.forEach((segment, index) => {
        const renderer = new google.maps.DirectionsRenderer({
            suppressMarkers: true,
            preserveViewport: true,
            polylineOptions: {
                strokeColor: segment.color,
                strokeWeight: 5,
                strokeOpacity: 0.9
            }
        });

        renderer.setMap(map);
        activeRenderers.push(renderer);

        directionsService.route({
            origin: segment.origin,
            destination: segment.destination,
            travelMode: segment.mode
        }, (result, status) => {
            if (status === "OK") {
                renderer.setDirections(result);

                const leg = result.routes[0].legs[0];

                totalDistance += leg.distance.value;
                totalDuration += leg.duration.value;

                // Collect full route path for proper zoom
                result.routes[0].overview_path.forEach(point => {
                    routePoints.push(point);
                });

                // Build segment HTML
                let segmentHTML = `
                    <div class="segment">
                        <div class="segment-header" onclick="toggleSegment(${index})">
                            ▶ ${segment.label}
                        </div>
                        <div id="segment-${index}" class="segment-steps hidden">
                `;

                leg.steps.forEach((step, i) => {
                    segmentHTML += `
                        <div class="step">
                            <strong>${i + 1}.</strong> ${step.instructions}<br>
                            <span class="step-distance">
                                ${step.distance.text}
                            </span>
                        </div>
                    `;
                });

                segmentHTML += `
                        </div>
                    </div>
                `;

                // Store in correct order
                segmentResults[index] = segmentHTML;

                completed++;

                // Only render AFTER all segments finish
                if (completed === segments.length) {
                    const km = (totalDistance / 1000).toFixed(2);
                    const mins = Math.round(totalDuration / 60);

                    const orderedHTML = segmentResults.join("");

                    document.getElementById("route-status").innerHTML = `
                        <div class="route-summary">
                             🚲 ${km} km • ⏱️ ${mins} mins
                        </div>

                        <div class="route-overview">
                            ${orderedHTML}
                        </div>
                    `;

                    // Show buttons
                    const actions = document.getElementById("route-actions");
                    if (actions) actions.style.display = "flex";

                    // Fit FULL route bounds
                    const bounds = new google.maps.LatLngBounds();
                    routePoints.forEach(point => bounds.extend(point));
                    map.fitBounds(bounds, 80);
                }

            } else {
                console.error("Segment failed:", status);
            }
        });
    });
}
// Display route overview & details
function toggleSegment(index) {
    const el = document.getElementById(`segment-${index}`);
    const header = el.previousElementSibling;

    if (el.classList.contains("hidden")) {
        el.classList.remove("hidden");
        header.innerText = "▼ " + header.innerText.replace("▶ ", "").replace("▼ ", "");
    } else {
        el.classList.add("hidden");
        header.innerText = "▶ " + header.innerText.replace("▶ ", "").replace("▼ ", "");
    }
}

// Clear route after use
function clearRoute() {
    activeRenderers.forEach(renderer => {
        renderer.setMap(null); // removes from map
    });

    activeRenderers = []; // reset array
    
    //clear click markers
    clickMarkers.forEach(m => m.setMap(null));
    clickMarkers = [];
    
    // clear route markers
    routeMarkers.forEach(marker => marker.setMap(null));
    routeMarkers = [];
    
    document.getElementById("route-status").innerText = "No route selected";

    // Clear start/end markers
    if (startMarker) {
        startMarker.setMap(null);
        startMarker = null;
    }

    if (endMarker) {
        endMarker.setMap(null);
        endMarker = null;
    }

    // Clear status
    // selectedStart = null;
    // selectedEnd = null;

}

document.addEventListener("DOMContentLoaded", () => {

    document.getElementById("close-drawer").addEventListener("click", closeDrawer);

    
    document.getElementById("route-btn").addEventListener("click", () => {
        if (!selectedStart || !selectedEnd) {
            alert("Please enter both your start point and destination");
            return;
        }
        calculateSmartRoute(selectedStart, selectedEnd);
    });
    document.getElementById("swap-btn").addEventListener("click", swapRoute);
    document.getElementById("reset-btn").addEventListener("click", resetRoute);

});

function getNearestStartStation(point) {
    let closest = null;
    let minDistance = Infinity;

    stations.forEach(station => {
        if (station.available_bikes <= 0) return; // skip ones without bikes

        const dist = Math.hypot(
            point.lat - Number(station.lat),
            point.lng - Number(station.lng)
        );

        if (dist < minDistance) {
            minDistance = dist;
            closest = station;
        }
    });

    return closest;
}

function getNearestEndStation(point) {
    let closest = null;
    let minDistance = Infinity;

    stations.forEach(station => {
        if (station.available_stands <= 0) return; // skip ones with nowhere to park

        const dist = Math.hypot(
            point.lat - Number(station.lat),
            point.lng - Number(station.lng)
        );

        if (dist < minDistance) {
            minDistance = dist;
            closest = station;
        }
    });

    return closest;
}

function initAutocomplete() {
    const startInput = document.getElementById("start-input");
    const endInput = document.getElementById("end-input");

    if (!startInput || !endInput) {
        console.error("Inputs not found");
        return;
    }

    const startAutocomplete = new google.maps.places.Autocomplete(startInput, {
        componentRestrictions: { country: "ie" }
    });

    const endAutocomplete = new google.maps.places.Autocomplete(endInput, {
        componentRestrictions: { country: "ie" }
    });

    startAutocomplete.addListener("place_changed", () => {
        infoWindow.close();
        const place = startAutocomplete.getPlace();

        if (!place.geometry) {
            alert("Please select a valid location");
            return;
        }

        selectedStart = {
            lat: place.geometry.location.lat(),
            lng: place.geometry.location.lng()
        };

        console.log("✅ Start set:", selectedStart);
        
    });

    endAutocomplete.addListener("place_changed", () => {
        const place = endAutocomplete.getPlace();

        if (!place.geometry) {
            alert("Please select a valid location");
            return;
        }

        selectedEnd = {
            lat: place.geometry.location.lat(),
            lng: place.geometry.location.lng()
        };

        console.log("🏁 End set:", selectedEnd);

    });
}

// If a user wants to swap their start and end points
function swapRoute() {
    if (!selectedStart || !selectedEnd) return;
    
    // Swap the locations
    [selectedStart, selectedEnd] = [selectedEnd, selectedStart];
    
    // Swap the text for the inputs
    const startInput = document.getElementById("start-input");
    const endInput = document.getElementById("end-input");
    
    [startInput.value, endInput.value] = [endInput.value, startInput.value];
    
    clearRoute();
    calculateSmartRoute(selectedStart, selectedEnd);
}

// Reset the screen
function resetRoute() {
    // Clear the route line
    clearRoute();
    
    // Reset values
    selectedStart = null;
    selectedEnd = null;
    
    // Clear the inputs in the drawer
    document.getElementById("start-input").value = "";
    document.getElementById("end-input").value = "";
    document.getElementById("route-status").innerText = "No route selected";
    
    // hide buttons
    const actions = document.getElementById("route-actions");
    if (actions) actions.style.display = "none";
    
}

// Account modal controls
document.addEventListener("DOMContentLoaded", () => {
    const accountBtn = document.getElementById("account-btn");
    const accountModal = document.getElementById("account-modal");
    const closeAccount = document.getElementById("close-account");
    const closeAccount2 = document.getElementById("close-account-2");

    if (accountBtn && accountModal) {
        accountBtn.addEventListener("click", () => {
            accountModal.style.display = "flex";
        });
    }

    if (closeAccount && accountModal) {
        closeAccount.addEventListener("click", () => {
            accountModal.style.display = "none";
        });
    }

    if (closeAccount2 && accountModal) {
        closeAccount2.addEventListener("click", () => {
            accountModal.style.display = "none";
        });
    }

    window.addEventListener("click", (e) => {
        if (e.target === accountModal) {
            accountModal.style.display = "none";
        }
    });
});

// Global map + info window variables
var map = null;
var infoWindow = null;

// Global Route Mapping variables
var directionsService = null;

// Required for Google Maps callback
window.initMap = initMap;
