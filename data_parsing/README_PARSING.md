# Data Parsing Documentation

## Overview

The `scrape_financial_vacancies_hh.py` script collects job vacancies from the financial and banking sector via HeadHunter.ru API and stores them in Parquet format for further processing.

## Implementation

The script implements the following workflow:

1. **API Connection**: Connects to HeadHunter.ru REST API using authenticated requests
2. **Category-based Search**: Queries vacancies across predefined financial job categories (financial analyst, banking specialist, etc.)
3. **Data Extraction**: Extracts structured information for each vacancy (title, description, salary, skills, location)
4. **Data Storage**: Serializes collected data to Parquet format using Polars library

## Technical Details

- **HTTP Client**: `requests` library for API communication
- **Data Format**: HeadHunter API returns JSON responses
- **Serialization**: Polars DataFrame serialization to Parquet format
- **Data Schema**: Structured schema with fields: title, company, location, salary, experience, description, key_skills, job_type, date_of_post, hh_url

## Dependencies

Required packages:
- `requests` - HTTP client for API requests
- `polars` - DataFrame library for data processing
- `tqdm` - Progress bar for long-running operations

Install via:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Execution

```bash
python data_parsing/scrape_financial_vacancies_hh.py
```

This collects vacancies across all regions (execution time: 30-60 minutes).

### Configuration

Modify parameters in `scrape_financial_vacancies_hh.py`:

```python
vacancies = scraper.scrape_all_financial_vacancies(
    area=1,              # 1 = Moscow, 2 = St. Petersburg, 113 = All Russia
    max_per_category=50  # Maximum vacancies per category
)
```

### API Token (Optional)

HeadHunter API token can be provided via:
```python
scraper = HHVacancyScraper(api_token="your_token")
```

Token can be obtained at: https://hh.ru/oauth/applications

## Output

The script generates:
- `data/financial_vacancies.parquet` - Structured vacancy data

## Data Schema

Each vacancy record contains:
- `idx` - Unique identifier
- `title` - Job title
- `company` - Company name
- `location` - City
- `salary` - Salary range (if specified)
- `experience` - Required experience level
- `description` - Job description
- `key_skills` - Required skills
- `job_type` - Employment type (full-time/part-time)
- `date_of_post` - Publication date
- `hh_url` - HeadHunter URL

## Rate Limiting

The script implements request throttling to comply with HeadHunter API limits:
- Default delay: 0.5 seconds between requests
- Automatic duplicate removal
- Error handling with retry logic

## Next Steps

After parsing:
1. Verify data integrity in `financial_vacancies.parquet`
2. Generate embeddings: `python data_parsing/generate_embeddings.py`
3. Load to database: Vacancies are automatically seeded on application startup

## Troubleshooting

**Connection timeout**: Check network connectivity, increase timeout parameter.

**Rate limit errors**: Increase `delay_seconds` parameter in `HHVacancyScraper` class.

**Low vacancy count**: Verify `FINANCIAL_CATEGORIES` are current, adjust search area, increase `max_per_category`.
