# WheelyWise

WheelyWise is a bike-sharing application that helps you find information about bike stations around Dublin. Whether you're searching for a station to pick up or drop off a bike, WheelyWise is the perfect application for you!

---

## Table of Contents

- [Features](#features)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Configuration](#configuration)
- [Usage](#usage)
- [Testing](#testing)
- [Contributing](#contributing)
- [Contact](#contact)

---

## Features

- **User Authentication**: Create an account and log in for a personalized experience.
- **Interactive Map**: View stations across Dublin on a map.
- **Navigation Assistance**: Get station addresses and directions from your current location.
- **Weather Forecast**: Check 24-hour weather information to plan your bike trips.
- **Bike Availability Trends**: Analyze bike availability trends for specific stations.

---

## Getting Started

### Prerequisites

Ensure you have Conda installed before proceeding. You can download it here:

[Conda Installation Guide](https://www.anaconda.com/docs/getting-started/miniconda/install)

### Installation

Follow these steps to set up WheelyWise:

1. **Create a Conda environment:**

   ```bash
   conda create -n your_env_name python=3.12
   ```

2. **Activate the environment:**

   ```bash
   conda activate your_env_name
   ```

3. **Clone the repository:**

   ```bash
   git clone git@github.com:davidirving98/COMP30830-SE-Project-Work.git
   ```

4. **Navigate to the project directory:**

   ```bash
   cd COMP30830-David
   ```

5. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
---

### Configuration

To configure the project, create a `.env` file in the root directory and add the following environment variables:

```env
JCDECAUX_API_KEY=your_jcdecaux_apikey
GOOGLE_MAPS_API_KEY=your_google_apikey
OPENWEATHER_API_KEY=your_open_weather_apikey

DB_ENV=local

# If using local database:
DB_DIALECT=mysql
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_db_password
DB_NAME=COMP30830_SW
```

---

## Usage

To run WheelyWise, follow these steps:

1. **Start the application:**

   ```bash
   python flaskapi/app.py
   ```

2. **Access the application** at `http://localhost:5000` in your browser.

3. **Sign up and log in** to use the app.

4. **Navigate to the map page** via the navigation bar.

For more advanced usage and API details, check out the documentation built with Sphinx in the `Sphinx_docs` directory:

```bash
cd Sphinx_docs
make html
```

---

## Testing

Run tests using the following command:

```bash
pytest tests/ -v
```

The testing suite covers various aspects of the application, including:

- **Flask App Tests** (`test_flask_app.py`):
  - Station routes (success & failure)
  - Weather/Forecast API integrations
  - Prediction endpoint validation
- **Frontend Logic Tests** (`test_frontend_index.py`):
  - Datetime formatting & UI updates
  - Map station marker color logic
  - Nearest station algorithms
- **Machine Learning Tests** (`test_machine_learning.py`):
  - Prediction payload validation
  - Prediction generation by station and datetime
- **Utility/Mocking Examples** (`testing-examples/`):
  - Calculator, string operations, and mock tests

---

## Contributing

We welcome contributions! To contribute, follow these steps:

1. **Fork the repository.**
2. **Create a new branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Commit your changes:**
   ```bash
   git commit -m "Add your feature"
   ```
4. **Push to the branch:**
   ```bash
   git push origin feature/your-feature-name
   ```
5. **Open a pull request.**

---

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Contact

For questions or feedback, feel free to reach out:

- **GitHub Issues**: [Open an Issue](https://github.com/davidirving98/COMP30830-SE-Project-Work/issues)

---

### Made by:

- Alex
- David
- Yian

