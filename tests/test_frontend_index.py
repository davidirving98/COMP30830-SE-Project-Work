import json
import shutil
import subprocess
import tempfile
import textwrap
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INDEX_JS_PATH = PROJECT_ROOT / "flaskapi" / "static" / "js" / "index.js"
NODE_BIN = shutil.which("node")


def run_frontend_assertions(assertions_js: str) -> None: # test helper to run JavaScript assertions in a Node.js environment with mocked DOM and APIs
    if NODE_BIN is None:
        pytest.skip("Node.js is required for frontend mock tests")

    script = textwrap.dedent(
        """
        const assert = require("node:assert/strict");
        const fs = require("fs");
        const vm = require("vm");

        const code = fs.readFileSync(__INDEX_JS__, "utf8");
        const elements = new Map();

        function makeElement(id) {
          return {
            id,
            value: "",
            innerText: "",
            textContent: "",
            innerHTML: "",
            style: { display: "" },
            classList: {
              add() {},
              remove() {},
              contains() { return false; },
            },
            addEventListener() {},
            appendChild() {},
            closest() { return null; },
            previousElementSibling: null,
          };
        }

        const document = {
          addEventListener() {},
          getElementById(id) {
            if (!elements.has(id)) {
              elements.set(id, makeElement(id));
            }
            return elements.get(id);
          },
          createElement(tag) {
            return makeElement(tag);
          },
          body: { appendChild() {} },
        };

        const ctx = {
          console,
          window: {},
          document,
          addEventListener() {},
          localStorage: {
            getItem() { return null; },
            setItem() {},
          },
          __alerts: [],
          __fetchCalls: [],
          __fetchResponse: null,
          fetch: async function (url) {
            ctx.__fetchCalls.push(url);
            if (typeof ctx.__fetchResponse === "function") {
              return await ctx.__fetchResponse(url);
            }
            if (ctx.__fetchResponse) {
              return ctx.__fetchResponse;
            }
            return {
              ok: true,
              status: 200,
              json: async () => ({}),
            };
          },
          alert: function (message) {
            ctx.__alerts.push(message);
          },
          google: {
            charts: {
              load() {},
              setOnLoadCallback(cb) {
                if (typeof cb === "function") cb();
              },
            },
            maps: {
              Size: function () {},
              Marker: function (opts) {
                this.opts = opts;
                this.map = null;
                this.listeners = {};
                this.setMap = (map) => { this.map = map; };
                this.addListener = (event, handler) => {
                  this.listeners[event] = handler;
                };
              },
              InfoWindow: function () {
                this.content = "";
                this.setContent = (content) => {
                  this.content = content;
                };
                this.open = function () {};
                this.close = function () {};
              },
              DirectionsService: function () {
                this.route = function () {};
              },
              Map: function () {
                this.addListener = function () {};
                this.panTo = function () {};
                this.setZoom = function () {};
                this.fitBounds = function () {};
              },
              Geocoder: function () {
                this.geocode = function () {};
              },
              TravelMode: {
                WALKING: "WALKING",
                BICYCLING: "BICYCLING",
              },
              event: {
                addListenerOnce() {},
                trigger() {},
              },
              places: {
                Autocomplete: function () {
                  return {
                    addListener() {},
                    getPlace() {
                      return {};
                    },
                  };
                },
              },
              LatLngBounds: function () {
                this.extend = function () {};
              },
              DirectionsRenderer: function () {
                return {
                  setMap() {},
                  setDirections() {},
                };
              },
            },
            visualization: {
              DataTable: function () {
                this.addColumn = function () {};
                this.addRows = function () {};
              },
              LineChart: function () {
                return {
                  draw() {},
                };
              },
            },
          },
        };

        ctx.window = ctx;
        vm.createContext(ctx);
        vm.runInContext(code, ctx);

        (async () => {
        __ASSERTIONS__
        })().catch((error) => {
          console.error(error);
          process.exit(1);
        });
        """
    ).replace("__INDEX_JS__", json.dumps(str(INDEX_JS_PATH)))
    script = script.replace("__ASSERTIONS__", textwrap.dedent(assertions_js))

    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as handle:
        handle.write(script)
        temp_path = handle.name

    try:
        completed = subprocess.run(
            [NODE_BIN, temp_path],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
        )
    finally:
        Path(temp_path).unlink(missing_ok=True)

    if completed.returncode != 0:
        raise AssertionError(
            "Frontend mock test failed\n"
            f"STDOUT:\n{completed.stdout}\n"
            f"STDERR:\n{completed.stderr}"
        )


def test_to_local_datetime_value_formats_expected_string(): # test time conversion utility function to toLocalDatetimeValue
    run_frontend_assertions(
        """
        const value = ctx.toLocalDatetimeValue(new Date(2026, 3, 9, 8, 5, 0));
        assert.equal(value, "2026-04-09T08:05");
        """
    )


def test_get_station_color_maps_availability_states(): # test station color mapping based on availability states
    run_frontend_assertions(
        """
        assert.equal(
          ctx.getStationColor({ available_bikes: 0, available_stands: 0 }),
          "grey"
        );
        assert.equal(
          ctx.getStationColor({ available_bikes: 0, available_stands: 5 }),
          "red"
        );
        assert.equal(
          ctx.getStationColor({ available_bikes: 4, available_stands: 0 }),
          "green"
        );
        assert.equal(
          ctx.getStationColor({ available_bikes: 4, available_stands: 5 }),
          "blue"
        );
        """
    )


def test_predict_by_input_validates_missing_inputs_without_fetch(): # test prediction input validation without making API calls to predictByInput() 
    run_frontend_assertions(
        """
        ctx.document.getElementById("predict-station-id").value = "";
        ctx.document.getElementById("predict-datetime").value = "";

        await ctx.predictByInput();

        assert.equal(ctx.__fetchCalls.length, 0);
        assert.equal(
          ctx.document.getElementById("predict-result").innerText,
          "Please enter station number and datetime."
        );
        """
    )


def test_predict_by_input_builds_api_request_and_updates_result():
    run_frontend_assertions(
        """
        ctx.document.getElementById("predict-station-id").value = "3";
        ctx.document.getElementById("predict-datetime").value = "2026-04-09T08:05";
        ctx.__fetchResponse = {
          ok: true,
          status: 200,
          json: async () => ({ pred_available_bikes: [6] }),
        };

        await ctx.predictByInput();

        assert.equal(
          ctx.__fetchCalls[0],
          "/predict/by-input?station_id=3&datetime=2026-04-09%2008%3A05%3A00"
        );
        assert.equal(
          ctx.document.getElementById("predict-result").innerText,
          "Predicted available bikes: 6"
        );
        """
    )


def test_load_current_weather_updates_summary_fields(): # test loading current weather data and updating the corresponding summary fields in the UI
    run_frontend_assertions(
        """
        ctx.__fetchResponse = {
          ok: true,
          status: 200,
          json: async () => ({
            temperature: 12.6,
            weather: "Clouds",
            wind_speed: 3.4,
            humidity: 81,
          }),
        };

        await ctx.loadCurrentWeather();

        assert.equal(ctx.__fetchCalls[0], "/weather");
        assert.equal(ctx.document.getElementById("temperature").textContent, "13°C");
        assert.equal(ctx.document.getElementById("weather").textContent, "Clouds");
        assert.equal(ctx.document.getElementById("wind_speed").textContent, "3m/s");
        assert.equal(ctx.document.getElementById("humidity").textContent, "81%");
        """
    )


def test_load_forecast_updates_two_cards(): # test loading weather forecast data and updating the corresponding cards in the UI
    run_frontend_assertions(
        """
        ctx.__fetchResponse = {
          ok: true,
          status: 200,
          json: async () => ([
            {
              forecast_time: "2026-04-09 09:00:00",
              temperature: 10.2,
              weather: "Clouds",
              humidity: 70,
            },
            {
              forecast_time: "2026-04-09 12:00:00",
              temperature: 14.8,
              weather: "Rain",
              humidity: 88,
            }
          ]),
        };

        await ctx.loadForecast();

        assert.equal(ctx.__fetchCalls[0], "/forecast");
        assert.equal(
          ctx.document.getElementById("forecast1-time").textContent,
          "2026-04-09 09:00:00"
        );
        assert.equal(ctx.document.getElementById("forecast1-temp").textContent, "10°C");
        assert.equal(ctx.document.getElementById("forecast1-desc").textContent, "Clouds");
        assert.equal(ctx.document.getElementById("forecast1-humidity").textContent, "💧 70%");
        assert.equal(
          ctx.document.getElementById("forecast2-time").textContent,
          "2026-04-09 12:00:00"
        );
        assert.equal(ctx.document.getElementById("forecast2-temp").textContent, "15°C");
        assert.equal(ctx.document.getElementById("forecast2-desc").textContent, "Rain");
        assert.equal(ctx.document.getElementById("forecast2-humidity").textContent, "💧 88%");
        """
    )


def test_get_nearest_start_and_end_station_ignore_unusable_candidates(): # test nearest station selection for route planning, logic ignores unusable candidates based on availability states
    run_frontend_assertions(
        """
        vm.runInContext(`
          stations = [
            { number: 1, name: "Full start", lat: "53.3500", lng: "-6.2600", available_bikes: 0, available_stands: 3 },
            { number: 2, name: "Best start", lat: "53.3490", lng: "-6.2590", available_bikes: 5, available_stands: 2 },
            { number: 3, name: "No stands", lat: "53.3485", lng: "-6.2585", available_bikes: 3, available_stands: 0 },
            { number: 4, name: "Best end", lat: "53.3510", lng: "-6.2570", available_bikes: 1, available_stands: 4 },
          ];
        `, ctx);

        const start = ctx.getNearestStartStation({ lat: 53.3492, lng: -6.2588 });
        const end = ctx.getNearestEndStation({ lat: 53.3508, lng: -6.2572 });

        assert.equal(start.number, 2);
        assert.equal(end.number, 4);
        """
    )
