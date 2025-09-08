# DateSpot Aggregator

A Python implementation of the n8n workflow that aggregates events from BlogTO, enriches them with location and weather data, categorizes them using AI, and publishes the results to GitHub.

## Features

- 📅 Fetches events from BlogTO API for the next 7 days
- ✅ Validates and cleans event data
- 📍 Adds location coordinates using Google Maps Geocoding API
- 🌤️ Enriches with weather data from Visual Crossing API
- 🤖 Categorizes events using Claude AI
- 🔽 Filters out unwanted categories (kids/seniors programs)
- 📤 Publishes final schema to GitHub repository

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure API keys:**
   ```bash
   # Copy the example environment file
   cp env.example .env
   
   # Edit with your actual API keys
   nano .env
   ```
   
   You'll need:
   - Google Maps Geocoding API key
   - Visual Crossing Weather API key  
   - Anthropic Claude API key
   - GitHub Personal Access Token

3. **API Setup Requirements:**
   - **Google Maps**: Enable Geocoding API in Google Cloud Console
   - **Visual Crossing**: Create account at visualcrossing.com
   - **Anthropic**: Get API key from console.anthropic.com
   - **GitHub**: Create Personal Access Token with repo permissions

## Usage

Run the complete workflow:

```bash
python main.py
```

The workflow will:
1. Fetch events from BlogTO for the next 7 days
2. Process and validate the data
3. Add coordinates and weather information
4. Categorize events using AI
5. Publish the final schema to your GitHub repository

## Configuration

All configuration is handled in `config.py`. Key settings:

- `FETCH_DAYS`: Number of days to fetch events (default: 7)
- `EXCLUDED_CATEGORIES`: Categories to filter out
- `REQUIRED_FIELDS`: Fields that must be present in events
- Rate limiting delays for API calls

## Project Structure

```
datespot-aggregator/
├── main.py                 # Main workflow orchestrator
├── config.py              # Configuration and API keys
├── requirements.txt        # Dependencies
├── services/              # API service modules
│   ├── blogto_api.py     # BlogTO events fetcher
│   ├── geocoding.py      # Google Maps geocoding
│   ├── weather.py        # Weather API integration
│   ├── ai_categorizer.py # Claude AI categorization
│   └── github_publisher.py # GitHub schema publisher
├── processors/           # Data processing modules
│   ├── data_validator.py # Data validation and cleaning
│   ├── schema_merger.py  # Data merging logic
│   └── filter.py         # Category filtering
└── utils/               # Utility modules
    ├── time_utils.py    # Time conversion utilities
    └── logger.py        # Logging configuration
```

## Output

The workflow produces a JSON schema with:
- **weather_report_by_date**: Weather data for each date
- **results_by_date**: Processed events with coordinates and categories

Events include:
- Basic info (title, description, venue, times)
- Location coordinates (lat/lng)
- Event category (AI-generated)
- Numerical time format for easy parsing

## Scheduling

For automated daily runs, use cron:

```bash
# Run daily at 2 AM
0 2 * * * cd /path/to/datespot-aggregator && python main.py
```

## Error Handling

The workflow includes comprehensive error handling:
- Failed API requests are logged but don't stop the workflow
- Invalid data is filtered out during validation
- Network timeouts are handled gracefully
- Detailed logging helps with troubleshooting

## Security

- API keys are loaded from .env file (never committed to git)
- Environment variables prevent hardcoded secrets
- GitHub tokens use least-privilege access
- No sensitive data is logged
- Rate limiting prevents API abuse
- .env file is automatically excluded from version control
