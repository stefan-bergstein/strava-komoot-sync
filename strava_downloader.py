#!/usr/bin/env python3
"""
Strava Activity Downloader
Downloads all activities from Strava API and saves them locally.
"""

import os
import json
import argparse
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import requests
from pathlib import Path


class StravaDownloader:
    """Handle Strava API authentication and activity downloads."""
    
    BASE_URL = "https://www.strava.com/api/v3"
    AUTH_URL = "https://www.strava.com/oauth/token"
    
    def __init__(self, client_id: str, client_secret: str, refresh_token: str):
        """Initialize with Strava API credentials."""
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[int] = None
        
    def authenticate(self) -> bool:
        """Get a fresh access token using the refresh token."""
        payload = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'refresh_token': self.refresh_token,
            'grant_type': 'refresh_token'
        }
        
        try:
            response = requests.post(self.AUTH_URL, data=payload)
            response.raise_for_status()
            data = response.json()
            
            self.access_token = data['access_token']
            self.token_expires_at = data['expires_at']
            
            print("✓ Successfully authenticated with Strava API")
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"✗ Authentication failed: {e}")
            return False
    
    def _ensure_authenticated(self):
        """Ensure we have a valid access token."""
        if not self.access_token or (self.token_expires_at is not None and datetime.now().timestamp() >= self.token_expires_at):
            if not self.authenticate():
                raise Exception("Failed to authenticate with Strava API")
    
    def get_activities(self, after: Optional[datetime] = None, 
                      before: Optional[datetime] = None,
                      per_page: int = 200) -> List[Dict]:
        """
        Fetch all activities within the specified date range.
        
        Args:
            after: Start date (inclusive)
            before: End date (inclusive)
            per_page: Number of activities per page (max 200)
            
        Returns:
            List of activity dictionaries
        """
        self._ensure_authenticated()
        
        headers = {'Authorization': f'Bearer {self.access_token}'}
        params = {'per_page': per_page, 'page': 1}
        
        if after:
            params['after'] = int(after.timestamp())
        if before:
            params['before'] = int(before.timestamp())
        
        all_activities = []
        
        print(f"Fetching activities...")
        
        while True:
            try:
                response = requests.get(
                    f"{self.BASE_URL}/athlete/activities",
                    headers=headers,
                    params=params
                )
                response.raise_for_status()
                activities = response.json()
                
                if not activities:
                    break
                
                all_activities.extend(activities)
                print(f"  Retrieved {len(all_activities)} activities so far...")
                
                params['page'] += 1
                
            except requests.exceptions.RequestException as e:
                print(f"✗ Error fetching activities: {e}")
                break
        
        print(f"✓ Total activities retrieved: {len(all_activities)}")
        return all_activities
    
    def get_activity_details(self, activity_id: int) -> Optional[Dict]:
        """
        Fetch detailed information for a specific activity.
        
        Args:
            activity_id: The Strava activity ID
            
        Returns:
            Detailed activity dictionary or None if failed
        """
        self._ensure_authenticated()
        
        headers = {'Authorization': f'Bearer {self.access_token}'}
        
        try:
            response = requests.get(
                f"{self.BASE_URL}/activities/{activity_id}",
                headers=headers
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"✗ Error fetching activity {activity_id}: {e}")
            return None


def save_activities(activities: List[Dict], output_dir: str, detailed: bool = False,
                   downloader: Optional[StravaDownloader] = None):
    """
    Save activities to local files.
    
    Args:
        activities: List of activity dictionaries
        output_dir: Directory to save activities
        detailed: Whether to fetch and save detailed activity data
        downloader: StravaDownloader instance (required if detailed=True)
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Save summary of all activities
    summary_file = output_path / "activities_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(activities, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved activities summary to {summary_file}")
    
    # Save individual activities
    activities_dir = output_path / "activities"
    activities_dir.mkdir(exist_ok=True)
    
    for i, activity in enumerate(activities, 1):
        activity_id = activity['id']
        activity_date = activity['start_date'][:10]  # YYYY-MM-DD
        activity_type = activity['type'].lower().replace(' ', '_')
        
        if detailed and downloader:
            print(f"  Fetching detailed data for activity {i}/{len(activities)}: {activity_id}")
            detailed_activity = downloader.get_activity_details(activity_id)
            if detailed_activity:
                activity = detailed_activity
        
        filename = f"{activity_date}_{activity_type}_{activity_id}.json"
        filepath = activities_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(activity, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Saved {len(activities)} individual activities to {activities_dir}")
    
    # Create a CSV summary for easy viewing
    csv_file = output_path / "activities_summary.csv"
    with open(csv_file, 'w', encoding='utf-8') as f:
        # Write header
        f.write("Date,Type,Name,Distance (km),Duration (min),Elevation Gain (m)\n")
        
        # Write data
        for activity in activities:
            date = activity['start_date'][:10]
            activity_type = activity['type']
            name = activity['name'].replace(',', ';')  # Avoid CSV issues
            distance = round(activity.get('distance', 0) / 1000, 2)  # Convert to km
            duration = round(activity.get('moving_time', 0) / 60, 2)  # Convert to minutes
            elevation = round(activity.get('total_elevation_gain', 0), 2)
            
            f.write(f"{date},{activity_type},{name},{distance},{duration},{elevation}\n")
    
    print(f"✓ Saved CSV summary to {csv_file}")


def load_credentials(config_file: str = "strava_config.json") -> Dict[str, str]:
    """Load Strava API credentials from config file."""
    config_path = Path(config_file)
    
    if not config_path.exists():
        print(f"✗ Config file not found: {config_file}")
        print("\nPlease create a strava_config.json file with your credentials:")
        print(json.dumps({
            "client_id": "YOUR_CLIENT_ID",
            "client_secret": "YOUR_CLIENT_SECRET",
            "refresh_token": "YOUR_REFRESH_TOKEN"
        }, indent=2))
        return {}
    
    with open(config_path, 'r') as f:
        return json.load(f)


def parse_date(date_str: str) -> datetime:
    """Parse date string in YYYY-MM-DD format."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid date format: {date_str}. Use YYYY-MM-DD")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Download Strava activities and save them locally",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download all activities
  python strava_downloader.py
  
  # Download activities from a specific date
  python strava_downloader.py --after 2024-01-01
  
  # Download activities within a date range
  python strava_downloader.py --after 2024-01-01 --before 2024-12-31
  
  # Download with detailed activity data
  python strava_downloader.py --detailed
  
  # Specify custom output directory
  python strava_downloader.py --output ./my_activities
        """
    )
    
    parser.add_argument(
        '--after',
        type=parse_date,
        help='Download activities after this date (YYYY-MM-DD)'
    )
    
    parser.add_argument(
        '--before',
        type=parse_date,
        help='Download activities before this date (YYYY-MM-DD)'
    )
    
    parser.add_argument(
        '--output',
        default='./strava_data',
        help='Output directory for downloaded activities (default: ./strava_data)'
    )
    
    parser.add_argument(
        '--config',
        default='strava_config.json',
        help='Path to config file with API credentials (default: strava_config.json)'
    )
    
    parser.add_argument(
        '--detailed',
        action='store_true',
        help='Fetch detailed data for each activity (slower but more complete)'
    )
    
    args = parser.parse_args()
    
    # Load credentials
    credentials = load_credentials(args.config)
    if not credentials:
        return 1
    
    # Validate credentials
    required_keys = ['client_id', 'client_secret', 'refresh_token']
    missing_keys = [key for key in required_keys if key not in credentials]
    if missing_keys:
        print(f"✗ Missing required credentials: {', '.join(missing_keys)}")
        return 1
    
    # Initialize downloader
    downloader = StravaDownloader(
        client_id=credentials['client_id'],
        client_secret=credentials['client_secret'],
        refresh_token=credentials['refresh_token']
    )
    
    # Authenticate
    if not downloader.authenticate():
        return 1
    
    # Display date range
    if args.after or args.before:
        date_range = []
        if args.after:
            date_range.append(f"after {args.after.strftime('%Y-%m-%d')}")
        if args.before:
            date_range.append(f"before {args.before.strftime('%Y-%m-%d')}")
        print(f"Date range: {' and '.join(date_range)}")
    else:
        print("Date range: All activities")
    
    # Fetch activities
    activities = downloader.get_activities(after=args.after, before=args.before)
    
    if not activities:
        print("No activities found.")
        return 0
    
    # Save activities
    save_activities(
        activities,
        args.output,
        detailed=args.detailed,
        downloader=downloader if args.detailed else None
    )
    
    print(f"\n✓ Successfully downloaded {len(activities)} activities to {args.output}")
    return 0


if __name__ == "__main__":
    exit(main())