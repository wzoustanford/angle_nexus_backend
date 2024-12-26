# Web Directory

This directory contains the core Flask web application for the `angle_backend` project. It includes all necessary modules, templates, and configurations to run the web app.

## Project Structure

```
web/
├── static/                # Static files (CSS, JS, images, etc.)
├── templates/             # HTML templates for the web app
├── __init__.py            # Initializes the Flask app and configuration
├── main.py                # Entry point for the web application
├── views.py               # Defines routes and logic for the app
```

## Requirements

Ensure you have the following installed:

1. **Python 3.9+**
2. **Virtual Environment**
3. **Flask** and other dependencies listed in `requirements.txt`

## Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/your-repo/angle_backend.git
   cd angle_backend/web
   ```

2. **Create and Activate a Virtual Environment**

   ```bash
   # Create a virtual environment
   python3 -m venv venv

   # Activate the virtual environment
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate    # Windows
   ```

3. **Install Dependencies**

   ```bash
   pip install -r ../requirements.txt
   ```

## Configuration

### Environment Variables

The application uses the `.flaskenv` file to manage configuration for development. Ensure the file exists at the root of `angle_backend` with the following content:

```env
FLASK_APP=web.main
FLASK_ENV=development
FLASK_RUN_PORT=5001
```

### Updating Paths Dynamically

The app dynamically resolves paths to ensure compatibility across operating systems. The datasets are located in the `data/` directory of the root project folder.

## Running the Application

1. **Using `flask run`**

   Ensure you're in the `angle_backend` directory and the virtual environment is activated. Then run:

   ```bash
   flask run
   ```

   The app will be available at `http://localhost:5001`.

2. **Using `python`**

   You can also run the app directly using Python. Navigate to the `web` directory and execute:

   ```bash
   python main.py
   ```

   The app will be available at `http://localhost:5001`.

## API Endpoints

### 1. `/companies`

- **Method**: GET
- **Description**: Queries crypto data for the term "bitcoin".
- **Example Response**:

  ```json
  [
    {"name": "Bitcoin", "price": 50000},
    {"name": "Bitcoin Cash", "price": 250}
  ]
  ```

### 2. `/equity-api`

- **Method**: GET, POST
- **Description**: Queries equity data based on the provided query parameter.
- **Query Parameter**: `query` (string)
- **Example**:

  ```bash
  curl -X GET 'http://localhost:5001/equity-api?query=Apple'
  ```

  **Example Response**:

  ```json
  [
    {"name": "Apple Inc.", "ticker": "AAPL", "price": 150}
  ]
  ```

### 3. `/crypto-api`

- **Method**: GET, POST
- **Description**: Queries crypto data based on the provided query parameter.
- **Query Parameter**: `query` (string)
- **Example**:

  ```bash
  curl -X GET 'http://localhost:5001/crypto-api?query=Bitcoin'
  ```

  **Example Response**:

  ```json
  [
    {"name": "Bitcoin", "price": 50000}
  ]
  ```

## Development Notes

### Static and Template Files
- Place static assets such as CSS, JavaScript, and images in the `static/` folder.
- HTML templates should reside in the `templates/` folder.

### Dataset Loading

Datasets are loaded dynamically from the `data/` directory in the root project folder. Ensure that the following files exist:

- `data/equity_nyse_exported_table.csv`
- `data/equity_nasdaq_exported_table.csv`
- `data/crypto_info_table_full.csv`

Paths are resolved using Python's `os.path` for cross-platform compatibility.

### Debugging

To enable Flask's debugging tools, set the `FLASK_ENV` environment variable to `development`.

## Future Improvements

1. **Add Unit Tests**: Implement unit tests for key functionalities.
2. **Improve Error Handling**: Provide meaningful error messages for invalid API requests.
3. **Deploy**: Containerize the application with Docker for deployment.

---

## License

This project is licensed under the MIT License. See the `LICENSE` file for more details.
