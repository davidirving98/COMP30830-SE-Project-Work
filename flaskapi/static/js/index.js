// Global array for storing the station data from the API
let stations = [];

// Initialise route mapping variables
let selectedStart = null;
let selectedEnd = null;
let currentStation = null;

// Load Google Charts once to speed up
google.charts.load('current', { packages: ['corechart'] });

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
                            const ts = new Date(String(item.last_update).replace(" ", "T"));
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

// Initialize and add the map
function initMap() {
    const dublin = { lat: 53.35014, lng: -6.266155 };

    map = new google.maps.Map(document.getElementById("map"), {
        zoom: 14,
        center: dublin,
    });

    // Single reusable information window
    infoWindow = new google.maps.InfoWindow();
    
    // Route Mapping
    directionsService = new google.maps.DirectionsService();
    directionsRenderer = new google.maps.DirectionsRenderer({
        suppressMarkers: false, // Keep the default markers
        polylineOptions: {
            strokeColor: "#2563eb",
            strokeWeight: 6,
            strokeOpacity: 0.9
        }
    });
    
    directionsRenderer.setMap(map);

    // Close any open station info window when you click elsewhere
    map.addListener("click", () => {
        infoWindow.close();
        resetRoute();
    });

    // Load station data
    getStations();
    
    initAutocomplete();
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

    // Show modal when page first loads only
    if (!localStorage.getItem("wheelyWelcomeSeen")) {
        welcomeModal.style.display = "flex";
        localStorage.setItem("wheelyWelcomeSeen", true);
    }

    // Close modal
    function closeModal() {
        welcomeModal.style.display = "none";
    }

    closeWelcome.addEventListener("click", closeModal);
    startBtn.addEventListener("click", closeModal);
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
    const bikes = document.getElementById("drawer-bikes");
    const stands = document.getElementById("drawer-stands");
    
    if (station) {
        currentStation = station;
    
    document.getElementById("drawer-title").innerText = station.name;
    document.getElementById("drawer-bikes").innerText = station.available_bikes;
    document.getElementById("drawer-stands").innerText = station.available_stands;
    } else {
    document.getElementById("drawer-title").innerText = "Route Planner";
    document.getElementById("drawer-bikes").innerText = "-";
    document.getElementById("drawer-stands").innerText = "-";     
    }
    
    drawer.classList.add("open");
}

function closeDrawer()  {
    document.getElementById("drawer").classList.remove("open");
}

// Routing Function
function calculateRoute(start, end) {
    clearRoute();
    
    directionsService.route({
        origin: start,
        destination: end,
        travelMode: google.maps.TravelMode.BICYCLING
    }, (result, status) => {
        
        if (status === "OK") {
            directionsRenderer.setDirections(result);
            
            document.getElementById("route-actions").style.display = "block";
            openDrawer();
            
            // Show Route info
            const route = result.routes[0].legs[0];
            
            const distance = route.distance.text;
            const duration = route.duration.text;
            
            const steps = result.routes[0].legs[0].steps;
            
            let directionsHTML = `<strong>🚲 ${distance} • ⏱️ ${duration}</strong><br><br>`;
            
            steps.forEach((step, i) => {
                directionsHTML += `${i + 1}. ${step.instructions} (${step.distance.text})<br>`;
            });
            
            document.getElementById("route-status").innerHTML = directionsHTML;
            
            map.fitBounds(result.routes[0].bounds);
            
            

        } else {
            alert("Could not calculate route, please try again.", status);
        }
    });
}

// Clear route after use
function clearRoute() {
    if (directionsRenderer) {
        directionsRenderer.setDirections({ routes: [] });
    }
}

document.addEventListener("DOMContentLoaded", () => {

    document.getElementById("close-drawer").addEventListener("click", closeDrawer);

    document.getElementById("set-start-btn").addEventListener("click", () => {
        if (!currentStation) return;

        selectedStart = {
            lat: Number(currentStation.lat),
            lng: Number(currentStation.lng)
        };

        document.getElementById("route-status").innerText =
            "Start: " + currentStation.name;

        console.log("✅ Start set:", currentStation.name);
    });

    document.getElementById("set-end-btn").addEventListener("click", () => {
        if (!currentStation || !selectedStart) {
            alert("Select a start station first");
            return;
        }

        selectedEnd = {
            lat: Number(currentStation.lat),
            lng: Number(currentStation.lng)
        };

        calculateRoute(selectedStart, selectedEnd);

        console.log("🗺️ Route drawn");

        selectedStart = null;
        selectedEnd = null;
    });
    
    document.getElementById("route-btn").addEventListener("click", () => {
        if (!selectedStart || !selectedEnd) {
            alert("Please enter both your start point and destination");
            return;
        }
        
        calculateRoute(selectedStart, selectedEnd);
    });

});

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
    
    function tryRoute() {
        if (selectedStart && selectedEnd) {
            console.log("🚀 Drawing route...");
            calculateRoute(selectedStart, selectedEnd);
        }
    }

    startAutocomplete.addListener("place_changed", () => {
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
    calculateRoute(selectedStart, selectedEnd);
}

// Reset the screen
function resetRoute() {
    // Clear the route line
    if (directionsRenderer) {
        directionsRenderer.setDirections({ routes: [] });
    }
    
    // Reset values
    selectedStart = null;
    selectedEnd = null;
    
    // Clear the inputs in the drawer
    document.getElementById("start-input").value = "";
    document.getElementById("end-input").value = "";
    document.getElementById("route-status").innerText = "No route selected";
    
    document.getElementById("route-actions").style.display = "none";
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
var directionsRenderer = null;

// Required for Google Maps callback
window.initMap = initMap;
