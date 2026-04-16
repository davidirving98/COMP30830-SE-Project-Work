# Unit Test Guide

> Last updated: 2026-04-16

This document describes the current test coverage in `tests/`, what each test validates, and how to run the suite.

## 1. How PASS Output Works

There are two useful output styles when running tests:

1. Standard pytest pass/fail summary.
2. Extra per-test PASS line from `tests/conftest.py`:
   - Format: `PASS: tests/xxx.py::test_xxx`
   - Trigger: printed when a test passes in the `call` phase.

To see print output from tests and hooks, run with `-s`:

```bash
pytest -s tests/
```

For compact output:

```bash
pytest -q tests/
```

## 2. Recommended Test Commands

Run all current unit tests:

```bash
pytest -s tests/
```

Run only backend route + ML tests:

```bash
pytest -s tests/test_flask_app.py tests/test_machine_learning.py
```

Run frontend JS unit tests only:

```bash
pytest -s tests/test_frontend_index.py
```

Quiet mode for CI/local quick checks:

```bash
pytest -q tests/
```

## 3. Current Test Files and Coverage

## 3.1 `tests/test_flask_app.py`

Target module: `flaskapi/app.py` (Flask route layer)

Coverage:

1. `test_weather_unavailable_returns_500`
- Condition: `get_weather()` mocked as `None`.
- Expected: `/weather` returns `500` with `{"error": "Weather API unavailable"}`.

2. `test_weather_success_returns_payload`
- Condition: `get_weather()` mocked with valid payload.
- Expected: `/weather` returns `200` with the same JSON.

3. `test_forecast_success_returns_payload`
- Condition: `get_forecast()` mocked with forecast list.
- Expected: `/forecast` returns `200` with the same JSON.

4. `test_stations_refresh_unavailable_returns_500`
- Condition: `fetch_stations_raw()` mocked as `None`.
- Expected: `/stations/refresh` returns `500` with bike API error.

5. `test_stations_refresh_success_returns_snapshot_result`
- Condition: refresh dependencies mocked to successful values.
- Expected: `/stations/refresh` returns `200` with write counters.

6. `test_stations_success_returns_payload`
- Condition: `get_latest_stations_view()` mocked with station list.
- Expected: `/stations` returns `200` with the same JSON.

7. `test_station_history_exception_returns_500`
- Condition: `get_station_history_sql()` raises exception.
- Expected: `/station/<id>/history` returns `500` and includes error text.

8. `test_predict_route_returns_service_result`
- Condition: `predict_from_payload()` mocked to `(payload, 200)`.
- Expected: `/predict` returns service payload and status.

9. `test_predict_by_input_invalid_query_returns_400`
- Condition: `parse_predict_query_args()` mocked to validation error.
- Expected: `/predict/by-input` returns `400` with error JSON.

Pass criteria:
- Correct HTTP status codes.
- Correct JSON shape/content.
- Correct route-level error handling.

## 3.2 `tests/test_machine_learning.py`

Target module: `flaskapi/ml_service.py`

Coverage:

1. `test_parse_predict_query_args_missing_returns_400`
- Condition: missing query parameters.
- Expected: function returns `(None, None, ({"error": ...}, 400))`.

2. `test_predict_from_payload_supports_single_record`
- Condition: single-record dict input, model mocked.
- Expected: prediction succeeds and returns target/raw/rounded prediction fields.

3. `test_predict_by_station_and_datetime_returns_basic_prediction`
- Condition: DB features + weather forecast mocked.
- Expected: returns `200` and payload includes station ID, predictions, and debug feature values.

Pass criteria:
- Correct status and response structure.
- Feature path can execute with mocked dependencies.

## 3.3 `tests/test_frontend_index.py`

Target module: `flaskapi/static/js/index.js`

Execution model:
- Tests run JavaScript assertions through Node.js using a mocked DOM and mocked browser APIs.
- If Node.js is not installed, these tests are skipped.

Coverage:

1. `test_to_local_datetime_value_formats_expected_string`
- Validates local datetime formatting to `YYYY-MM-DDTHH:mm`.

2. `test_get_station_color_maps_availability_states`
- Validates color mapping for station availability combinations.

3. `test_predict_by_input_validates_missing_inputs_without_fetch`
- Validates form validation branch: no fetch call when required input is missing.

4. `test_predict_by_input_builds_api_request_and_updates_result`
- Validates query-string construction and UI update after successful prediction response.

5. `test_load_current_weather_updates_summary_fields`
- Validates `/weather` fetch handling and summary field rendering.

6. `test_load_forecast_updates_two_cards`
- Validates `/forecast` fetch handling and rendering of two forecast cards.

7. `test_get_nearest_start_and_end_station_ignore_unusable_candidates`
- Validates nearest-station selection logic while filtering unusable candidates.

Pass criteria:
- Expected fetch calls are made (or intentionally not made).
- Expected DOM fields are updated with expected text values.
- Selection logic returns the expected station objects.

## 4. Notes

- This guide only documents test files that currently exist in `tests/`.
- Archived or removed historical test modules are intentionally excluded to avoid confusion.
