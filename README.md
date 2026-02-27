# Strava to Komoot Activity Sync

A comprehensive Python tool to download activities from Strava and sync them to Komoot. Features include date range filtering, GPX export, automatic activity type mapping, and intelligent fallback mechanisms.

## 🌟 Features

### Strava Integration
- ✅ Download all your Strava activities with metadata
- ✅ Export GPX files with smart fallback (official API + stream generation)
- ✅ Filter by date range (after/before dates)
- ✅ Filter by activity type (rides, runs, hikes, etc.)
- ✅ Save activities as JSON files with CSV summary
- ✅ OAuth2 authentication with refresh tokens
- ✅ Automatic pagination for large activity lists

### Komoot Integration
- ✅ Automatically upload activities to Komoot as tours
- ✅ Smart sport type mapping (Strava → Komoot)
- ✅ List and manage Komoot tours
- ✅ Sync tracking to prevent duplicates

### Advanced Features
- ✅ Modular, maintainable code architecture
- ✅ Intelligent GPX generation from activity streams when export fails
- ✅ Batch processing with progress tracking
- ✅ Comprehensive error handling and logging

## 📋 Prerequisites

- Python 3.7 or higher
- Strava account with API access
- Komoot account (for sync functionality)

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Navigate to project directory
cd strava

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure API Credentials

Create a configuration file:

```bash
python sync.py config --init
```

This creates `config.json`. Edit it with your credentials:

```json
{
  "strava": {
    "client_id": "YOUR_STRAVA_CLIENT_ID",
    "client_secret": "YOUR_STRAVA_CLIENT_SECRET",
    "refresh_token": "YOUR_STRAVA_REFRESH_TOKEN"
  },
  "komoot": {
    "email": "YOUR_KOMOOT_EMAIL",
    "password": "YOUR_KOMOOT_PASSWORD"
  }
}
```

### 3. Get Strava API Credentials

1. Go to [Strava API Settings](https://www.strava.com/settings/api)
2. Create an application:
   - **Application Name**: Choose any name (e.g., "Activity Sync Tool")
   - **Category**: Choose appropriate category
   - **Website**: Can be `http://localhost`
   - **Authorization Callback Domain**: Use `localhost`
3. Note your **Client ID** and **Client Secret**

### 4. Get Strava Refresh Token

1. Open this URL in your browser (replace `YOUR_CLIENT_ID`):
   ```
   https://www.strava.com/oauth/authorize?client_id=YOUR_CLIENT_ID&response_type=code&redirect_uri=http://localhost&approval_prompt=force&scope=activity:read_all
   ```

2. Authorize the application. You'll be redirected to a URL like:
   ```
   http://localhost/?state=&code=AUTHORIZATION_CODE&scope=read,activity:read_all
   ```

3. Copy the `AUTHORIZATION_CODE` from the URL

4. Exchange the authorization code for a refresh token:
   ```bash
   curl -X POST https://www.strava.com/oauth/token \
     -d client_id=YOUR_CLIENT_ID \
     -d client_secret=YOUR_CLIENT_SECRET \
     -d code=AUTHORIZATION_CODE \
     -d grant_type=authorization_code
   ```

5. The response will contain your `refresh_token`:
   ```json
   {
     "token_type": "Bearer",
     "expires_at": 1234567890,
     "expires_in": 21600,
     "refresh_token": "YOUR_REFRESH_TOKEN",
     "access_token": "YOUR_ACCESS_TOKEN",
     ...
   }
   ```

6. Copy the `refresh_token` value into your `config.json`

## 📖 Usage

### List Activities

List activities from Strava:
```bash
python sync.py list strava
python sync.py list strava --after 2024-01-01 --before 2024-12-31
```

List tours from Komoot:
```bash
python sync.py list komoot
```

### Download Activities from Strava

Download all activities:
```bash
python sync.py download
```

Download with date range:
```bash
python sync.py download --after 2024-01-01 --before 2024-12-31
```

Download and export GPX files:
```bash
python sync.py download --export-gpx --output ./my_activities
```

### Sync Activities to Komoot

Sync all activities from a date range:
```bash
python sync.py sync --after 2024-01-01 --before 2024-12-31
```

Sync specific activities by ID:
```bash
python sync.py sync --activity-ids 12345678,87654321
```

Sync only specific activity types:
```bash
python sync.py sync --types Ride,Run --after 2024-01-01
```

Override sport type for all activities:
```bash
python sync.py sync --sport mtb --after 2024-01-01
```

## 🎯 Command Reference

### `config` - Manage Configuration

```bash
python sync.py config --init
```

Creates an example `config.json` file with placeholders for your credentials.

### `list` - List Activities

```bash
python sync.py list {strava|komoot} [OPTIONS]

Options:
  --after DATE          List activities after this date (YYYY-MM-DD)
  --before DATE         List activities before this date (YYYY-MM-DD)
```

### `download` - Download Strava Activities

```bash
python sync.py download [OPTIONS]

Options:
  --after DATE          Download activities after this date (YYYY-MM-DD)
  --before DATE         Download activities before this date (YYYY-MM-DD)
  --output DIR          Output directory (default: ./strava_data)
  --export-gpx          Export activities as GPX files
```

### `sync` - Sync Activities to Komoot

```bash
python sync.py sync [OPTIONS]

Options:
  --after DATE          Sync activities after this date (YYYY-MM-DD)
  --before DATE         Sync activities before this date (YYYY-MM-DD)
  --activity-ids IDS    Comma-separated list of Strava activity IDs
  --types TYPES         Comma-separated list of activity types (e.g., Ride,Run)
  --sport SPORT         Override Komoot sport type for all activities
  --log-file FILE       Path to sync log file (default: sync_log.json)
```

## 🗺️ Sport Type Mapping

The tool automatically maps Strava activity types to Komoot sport types:

| Strava Type | Komoot Sport |
|-------------|--------------|
| Ride | touringbicycle |
| VirtualRide | touringbicycle |
| EBikeRide | e_touringbicycle |
| MountainBikeRide | mtb |
| GravelRide | mtb |
| RoadBike | racebike |
| Run | jogging |
| TrailRun | jogging |
| Walk | hiking |
| Hike | hiking |

You can override this mapping using the `--sport` option.

## 📁 Output Structure

### Download Command Output

```
strava_data/
├── activities_summary.json      # All activities in one JSON file
├── activities_summary.csv       # CSV summary for easy viewing
├── activities/                  # Individual activity files
│   ├── 2024-01-15_run_12345678.json
│   ├── 2024-01-16_ride_12345679.json
│   └── ...
└── gpx/                        # GPX files (if --export-gpx used)
    ├── 2024-01-15_run_12345678.gpx
    ├── 2024-01-16_ride_12345679.gpx
    └── ...
```

### Sync Log

The tool maintains a `sync_log.json` file that tracks:
- Which activities have been synced
- When they were synced
- Success/failure status
- Komoot tour IDs

This prevents duplicate uploads when running sync multiple times.

## 📁 Project Structure

```
strava/
├── src/
│   └── strava_komoot_sync/
│       ├── __init__.py
│       ├── cli.py                 # Command-line interface
│       ├── sync_manager.py        # Sync orchestration
│       ├── api/
│       │   ├── __init__.py
│       │   ├── strava_client.py   # Strava API client
│       │   └── komoot_client.py   # Komoot API client (via kompy)
│       └── utils/
│           ├── __init__.py
│           └── config.py          # Configuration management
├── sync.py                        # Main entry point
├── requirements.txt               # Python dependencies
├── config.json                    # Your configuration (create this)
├── sync_log.json                  # Sync history (auto-generated)
├── LICENSE                        # MIT License
└── README.md                      # This file
```

## 🔧 Technical Details

### GPX Export Strategy

The tool uses a two-tier approach for GPX export:

1. **Primary**: Try Strava's official GPX export endpoint
2. **Fallback**: If that fails, generate GPX from activity streams (GPS data)

This ensures maximum compatibility - even activities that don't support direct GPX export can still be synced.

### Dependencies

- `requests` - HTTP client for API calls
- `kompy` - Komoot API integration
- `gpxpy` - GPX file parsing and generation

## 🔒 Security Notes

- **Never commit `config.json`** - it contains sensitive credentials
- The `.gitignore` file is configured to exclude sensitive files
- Keep your API credentials private
- Strava refresh tokens don't expire but can be revoked
- Use environment variables for CI/CD pipelines

## 🐛 Troubleshooting

### Authentication Errors

**Strava:**
- Verify your credentials in `config.json`
- Ensure your refresh token is valid
- Check that your API application has `activity:read_all` scope
- Make sure the authorization callback domain is set to `localhost`

**Komoot:**
- Verify your email and password in `config.json`
- Komoot uses basic authentication (email/password)
- Ensure your Komoot account is active

### Rate Limiting

**Strava API Limits:**
- 100 requests per 15 minutes
- 1,000 requests per day

The tool handles pagination automatically but may hit limits with large syncs. If you encounter rate limits, wait 15 minutes and try again.

### GPX Export Issues

The message "Using activity streams to generate GPX..." is **normal** - it means the fallback mechanism is working. Strava's GPX export endpoint doesn't work for all activities, so the tool automatically generates GPX from GPS data streams.

If GPX generation fails:
- Ensure the activity has GPS data (virtual activities may not)
- Check that the activity is not private
- Verify your API permissions include activity data access

### Komoot Upload Issues

If uploads fail:
- Verify your Komoot credentials in `config.json`
- Check that the GPX file is valid
- Ensure you have storage space in your Komoot account
- Try uploading a single activity first to test

### No Activities Found

If no activities are found:
- Check your date range filters
- Verify you have activities in your Strava account
- Ensure your API application has the correct permissions
- Try listing activities without filters first

## 📊 Example Workflows

### Backup All Activities

```bash
# Download everything with GPX files
python sync.py download --export-gpx --output ./backup
```

### Sync Recent Rides

```bash
# Sync only bike rides from the last month
python sync.py sync --types Ride,MountainBikeRide --after 2024-11-01
```

### Migrate Specific Activities

```bash
# Get activity IDs first
python sync.py list strava --after 2024-01-01

# Sync specific activities
python sync.py sync --activity-ids 12345678,87654321,11223344
```

### Sync All Activities from a Year

```bash
# Sync all 2024 activities
python sync.py sync --after 2024-01-01 --before 2024-12-31
```

## 🤝 Contributing

This is a personal tool, but feel free to fork and modify for your needs. Contributions and improvements are welcome!

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details.

This tool is provided as-is for personal use. Please respect Strava and Komoot API terms of service and rate limits.

## 🔗 API Documentation

- [Strava API Documentation](https://developers.strava.com/docs/reference/)
- [Strava Getting Started Guide](https://developers.strava.com/docs/getting-started/)
- [Komoot API Documentation](https://developers.komoot.com/)
- [kompy Library](https://github.com/ThePyrotechnic/kompy)

## ⚠️ Disclaimer

This tool is not officially affiliated with Strava or Komoot. Use at your own risk and respect API rate limits and terms of service.

## 🙏 Acknowledgments

- Built with [kompy](https://github.com/ThePyrotechnic/kompy) for Komoot API integration
- Uses [gpxpy](https://github.com/tkrajina/gpxpy) for GPX file handling