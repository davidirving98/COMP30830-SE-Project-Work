# Diff Report: `main` vs `David`

Generated at: 2026-03-08 12:16:53 GMT  
Repository: `COMP30830-SE-Project-Work`

## 1) Comparison Scope

- Base branch: `main`
- Compare branch: `David`
- Merge base commit: `a8b3c8a0c49bee69fcbcb68f77938dcef72bc76f`
- Git range used: `main...David`

## 2) Commit-Level Difference

### Commits in `David` but not in `main`
- `851586cfb54a22e53f3bc16e53507dbab71ef579`  
  Author: `davidirving98`  
  Date: `Sat Mar 7 19:42:46 2026 +0000`  
  Message: `Initial website setup with JavaScript`

### Commits in `main` but not in `David`
- None

## 3) File-Level Difference Summary

`22 files changed, 991 insertions(+), 42 deletions(-)`

### Changed files (`main...David`)
- `M` `bikeinfo/.DS_Store`
- `M` `bikeinfo/data/.DS_Store`
- `M` `config.py`
- `A` `flaskapi/.DS_Store`
- `M` `flaskapi/app.py`
- `A` `flaskapi/static/.DS_Store`
- `M` `flaskapi/static/css/home.css`
- `A` `flaskapi/static/icons/.DS_Store`
- `A` `flaskapi/static/icons/apple-pay.svg`
- `A` `flaskapi/static/icons/bike-blue.svg`
- `A` `flaskapi/static/icons/bike-green.svg`
- `A` `flaskapi/static/icons/bike-grey.svg`
- `A` `flaskapi/static/icons/bike-red.svg`
- `A` `flaskapi/static/icons/bike.svg`
- `A` `flaskapi/static/icons/google-pay.svg`
- `A` `flaskapi/static/icons/map-pin.svg`
- `A` `flaskapi/static/icons/user.svg`
- `A` `flaskapi/static/js/index.js`
- `A` `flaskapi/templates/.DS_Store`
- `D` `flaskapi/templates/home.html`
- `A` `flaskapi/templates/index.html`
- `A` `weatherinfo/.DS_Store`

## 4) Key Functional Changes

### Backend (`flaskapi/app.py`)
- Root route handler renamed from `home()` to `index()`.
- Root template changed from `home.html` to `index.html`.
- `config` is imported and `apikey=config.GOOGLE_MAPS_API_KEY` is passed into template rendering.
- Import path handling for `config` was hardened:
  - Replaced `sys.path.append("..")` with a `Path(__file__).resolve().parents[1]`-based project-root insertion into `sys.path`.
  - This avoids `ModuleNotFoundError: No module named 'config'` when launching `app.py` from different working directories.

### Configuration (`config.py`)
- Added:
  - `GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")`

### Frontend Templates
- `flaskapi/templates/home.html` removed.
- New `flaskapi/templates/index.html` added with a large map-first UI:
  - top weather bar
  - bottom status/search/account bar
  - welcome modal and account modal
  - includes Google Charts loader and Google Maps JS API script
  - loads new `static/js/index.js`

### Frontend JS
- New `flaskapi/static/js/index.js` added:
  - Fetches `/stations`
  - Renders Google Maps markers with color logic based on bike/stand availability
  - Opens info window with chart per station (Google Charts)
  - Calculates and updates bottom-bar summary stats
  - Adds station search + zoom-to-marker behavior
  - Uses localStorage flag for first-load welcome modal

### Frontend CSS
- `flaskapi/static/css/home.css` significantly expanded (+400 lines range):
  - layout for fixed top bar, full-screen map region, fixed bottom bar
  - modal/account/welcome styling
  - search dropdown and station stats UI styling

## 5) Notable Risks / Review Notes

- `index.html` currently contains hardcoded weather/account demo values (not dynamic data-bound).
- Multiple `.DS_Store` files are included in the diff; these are usually unneeded in version control.
- `config` import path issue in `flaskapi/app.py` has been patched locally to use a file-location-based project root path.
- Google Maps depends on `GOOGLE_MAPS_API_KEY` being set in environment; missing key will break map initialization.

## 6) Quick Conclusion

`David` is ahead of `main` by one commit and introduces a substantial UI upgrade centered on Google Maps + station interactivity, along with template/route changes and API key configuration.

Additionally, a local follow-up fix was applied in `flaskapi/app.py` to make `config` imports stable regardless of launch directory.
