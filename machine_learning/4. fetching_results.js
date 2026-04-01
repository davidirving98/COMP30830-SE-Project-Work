const date = "2024-02-25";
const time = "09:00:00";
const station_id = 32;

fetch(`/predict?date=${date}&time=${time}&station_id=${station_id}`, {
    method: "GET"
})
    .then(response => response.json())
    .then(data => console.log("Prediction:", data.predicted_available_bikes))
    .catch(error => console.error("Error:", error));
    
    
