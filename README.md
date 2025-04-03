# Data Processing API

This Django API enables automatic processing of data files (CSV, JSON) by providing various data cleaning and preprocessing functionalities.

## Features

### File Management
- Upload CSV and JSON files
- Automatic data format validation
- Data preview
- Export processed data to CSV, JSON, or Excel

### Data Processing
- Detection and handling of missing values
  - Mode for categorical variables
  - Mean/Median for numerical variables
  - Specific handling for binary variables
- Identification and treatment of outliers
  - IQR (Interquartile Range) method
  - Preservation of original data types
- Normalization of numerical data
  - Min-Max normalization [0,1]
  - Proportion preservation
- Duplicate removal
- Target column support (for supervised learning)

## Prerequisites

- Python 3.8+
- Django 4.0+
- pandas
- numpy

## Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd data-processing-API
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Unix/macOS
venv\Scripts\activate    # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Apply migrations:
```bash
python manage.py migrate
```

5. Create a superuser (optional):
```bash
python manage.py createsuperuser
```

## Usage

1. Start the server:
```bash
python manage.py runserver
```

2. Access the web interface: http://localhost:8000

3. Data processing workflow:
   - Upload a file (CSV or JSON)
   - View metadata (number of rows, columns, missing values)
   - Configure processing options
   - Run the processing
   - Export processed data

## Project Structure

```
data-processing-API/
├── data_processor/           # Main application
│   ├── forms.py             # Configuration forms
│   ├── models.py            # Data models
│   └── views.py             # Processing logic
├── templates/               # HTML templates
├── static/                  # Static files
├── media/                   # Uploaded files
└── requirements.txt         # Dependencies
```

## Security

- File type validation
- File size limitation
- Secure storage of uploaded files
- CSRF protection

## Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Suggest improvements
- Submit pull requests

## License

This project is licensed under the MIT License. See the LICENSE file for details.