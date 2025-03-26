# Data Processing API

## Objective
Create a REST API for data processing and analysis, allowing users to perform statistical operations on datasets.

## Features

### Data Management
- Upload data files (CSV, JSON)
- Automatic data format validation
- Detection and handling of missing values
- Identification and processing of outliers
- Duplicate removal
- Data normalization

### Statistical Analysis
- Descriptive statistics (mean, median, standard deviation)
- Distribution analysis
- Correlation detection
- Basic statistical tests

### Visualization
- Graph generation (histograms, box plots)
- Export visualizations in PNG/PDF formats
- Customization of visual parameters

## Technologies
- Python 3.x
- FastAPI for REST API
- Pandas for data processing
- NumPy for statistical calculations
- Matplotlib/Seaborn for visualizations
- SQLite for storage

## Project Structure
```
data-processing-API/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── routes/
│   │   └── data_routes.py    # API Endpoints
│   ├── models/
│   │   └── data_models.py    # Pydantic Models
│   ├── services/
│   │   └── data_service.py   # Business Logic
│   └── utils/
│       └── data_processing.py # Utility Functions
├── tests/
│   ├── test_data_processing.py
│   └── test_data_service.py
├── data/
└── requirements.txt
```

## Installation
1. Clone the repository
   ```bash
   git clone [repo-url]
   cd data-processing-API
   ```

2. Create a virtual environment
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   .\venv\Scripts\activate  # Windows
   ```

3. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

4. Start the API
   ```bash
   uvicorn app.main:app --reload
   ```

## API Usage

### Data Upload
```python
POST /api/v1/data/upload
Content-Type: multipart/form-data

# Response
{
    "status": "success",
    "file_id": "abc123",
    "rows_count": 1000
}
```

### Statistical Analysis
```python
GET /api/v1/data/{file_id}/stats

# Response
{
    "mean": 42.5,
    "median": 41.0,
    "std": 5.2,
    "missing_values": 10
}
```

## Tests
Unit tests cover:
- Data validation
- Statistical processing
- API endpoints

Run tests:
```bash
python -m pytest tests/
```

## API Documentation
Complete API documentation is available at `/docs` once the server is running.
Includes:
- Detailed endpoint descriptions
- Request/response schemas
- Usage examples
- Error codes

## Contributing
1. Fork the project
2. Create a branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request