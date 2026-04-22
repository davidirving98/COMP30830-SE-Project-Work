# ML, Routing, Testing, and Frontend Chat Summary


## Topic 1: Splitting ML Logic out of `app.py`
User:
- The ML model section should be moved into a separate Python file so `app.py` keeps only routes and interface calls.

Assistant:
- Reviewed the original Flask structure.
- Identified the architecture split points:
  - `flaskapi/app.py` keeps route-level handling
  - `flaskapi/ml_service.py` contains model loading, feature engineering, and prediction flow

Result:
- Difference point:
  - before: route logic and ML logic were mixed in `app.py`
  - after the discussed refactor direction: `app.py` is route-focused and `ml_service.py` is prediction-focused

## Topic 2: Time Handling and DST in Prediction
User:
- Check whether time-related prediction APIs are consistent and whether DST can cause a 1-hour offset.

Assistant:
- Traced the full prediction time path from frontend input to backend parsing, DB lookup, and forecast matching.
- Confirmed prediction time should be interpreted in Dublin local time and converted to UTC before matching DB rows or forecasts.
- Identified the key code locations involved in the time-basis difference:
  - `flaskapi/ml_service.py`
  - `flaskapi/openweather.py`

Result:
- Difference point:
  - before: local/UTC handling could drift
  - after the discussed alignment: prediction time, DB lookup, and forecast matching use one consistent basis

## Topic 3: Weather Data in Display vs Model Input
User:
- Where is weather used for display, and where is it used for prediction features?

Assistant:
- Separated the two paths:
  - display path through `/weather` and `/forecast`
  - model path through forecast matching in `ml_service.py`
- Confirmed that some weather fields such as `pressure` were returned by the backend but not actually rendered by the frontend.

Result:
- The user-facing weather flow and ML feature flow were clearly separated.

## Topic 4: Logging, Routes, and Startup Behavior
User:
- What is actually logged on the backend?
- Which DB-related routes are really needed?
- Can startup automatically trigger data refresh/import?

Assistant:
- Confirmed that most backend failures are returned as JSON rather than written as explicit app logs.
- Explained the purpose of the DB routes and distinguished real frontend routes from debug-only routes.
- Identified the startup-related location and difference point:
  - `flaskapi/app.py`
  - difference discussed: app startup can include importer launch rather than relying only on manual execution

Result:
- Backend route purpose, logging behavior, and startup importer flow became clearer.

## Topic 5: Prediction Debug Output
User:
- Add debug information so prediction results can be analyzed when they look wrong.

Assistant:
- Identified the debug-response location and difference points in `flaskapi/ml_service.py`.
- The debug content discussed in the conversation included:
  - actual feature values sent to the model
  - matched forecast time
  - DB-derived history statistics
- Clarified that the large response size came from nested debug content rather than unexpected extra top-level fields.

Result:
- Difference point:
  - prediction responses can expose internal feature/forecast/DB context for debugging when needed

## Topic 6: Why Predictions Look Wrong
User:
- Some predictions are far from the real value. Why?

Assistant:
- Found a humidity-feature bug where a binary feature was accidentally being turned into `90`, which distorted predictions.
- Explained that even current-time prediction may still differ from the current live value because the model uses:
  - historical averages
  - weather context
  - station/time features
  rather than the exact live bike count at that moment.

Result:
- Difference point:
  - humidity handling in the prediction feature path was identified as a source of distorted output
  - the remaining gap to live values was explained by the historical/context-based feature design

## Topic 7: Missing `bikes_1d_mean` and 7-Day Forecasts
User:
- When predicting 7 days later, many outputs are too low or become `0`. Is that because `bikes_1d_mean` is missing?

Assistant:
- Confirmed that this can happen because the 1-day backward window before a future target time often has no rows in the DB.
- Explained that the old fallback to `0` was too aggressive.
- Identified the fallback location and difference point in `flaskapi/ml_service.py`:
  - `bikes_1d_mean` falls back to `bikes_same_slot_mean`
  - only then falls back to `0`

Result:
- Difference point:
  - before: missing `bikes_1d_mean` could collapse directly to `0`
  - after the discussed minimal fallback: `bikes_same_slot_mean` is used first

## Topic 8: LR vs Ridge and Model Loading Issues
User:
- Why did Linear Regression previously explode but now seems more bounded?
- Confirm whether the app is actually loading LR or Ridge.

Assistant:
- Reviewed `machine_learning/ML.ipynb` and connected the notebook conclusions to the online inference path.
- Explained why OLS/Linear Regression can produce huge raw outputs:
  - no natural output bounds
  - multicollinearity
  - out-of-distribution sensitivity
- Checked the runtime model object directly.
- Identified a model-loading mismatch in `flaskapi/ml_service.py` where `MODEL_PATH` could point at a `*_meta.joblib` file, which would load a `dict` instead of a model and cause:
  - `'dict' object has no attribute 'predict'`
- Compared actual runtime behavior of Ridge and LR after the fix.

Result:
- Difference point:
  - model file path and meta file path must stay separate
  - LR/Ridge runtime behavior was compared against the notebook conclusions

## Topic 9: Unit Tests and Frontend Mock Tests
User:
- Update the tests so they match the refactored backend.
- Also add frontend unit-style tests using mocks.

Assistant:
- Identified the active backend test locations:
  - `tests/test_flask_app.py`
  - `tests/test_machine_learning.py`
- Identified the test-style difference points:
  - Flask route tests use `mock/patch`
  - frontend mock tests cover:
  - time formatting
  - station color mapping
  - prediction input validation
  - prediction request building
  - weather rendering
  - forecast rendering
  - nearest station selection for route planning
- `tests/UNIT_TEST_GUIDE.md` was also used as the matching documentation location for these changes.

Result:
- Difference point:
  - backend tests and frontend mock coverage were aligned with the refactored structure

## Topic 10: DB URL Parsing and SQLAlchemy Fixes
User:
- Some DB scripts fail after password changes, especially when special characters like `@` are used.

Assistant:
- Identified broken DB URL parsing caused by manual string assembly.
- Identified the code difference point across DB/import helpers:
  - manual string-built SQLAlchemy URLs
  - versus `sqlalchemy.engine.URL.create(...)`

Result:
- Difference point:
  - DB connection handling became safer for passwords containing reserved URL characters

## Final Project-Relevant Outcomes
- ML logic extracted from `app.py` into `ml_service.py`
- prediction time flow aligned to avoid DST mismatch
- startup importer location and behavior clarified in `flaskapi/app.py`
- prediction debug response location and fields clarified in `flaskapi/ml_service.py`
- history-feature fallback simplified for missing `bikes_1d_mean`
- model-loading errors diagnosed and corrected
- backend tests and frontend mock tests aligned with the current codebase
- SQLAlchemy DB URL construction differences clarified for special-character passwords
