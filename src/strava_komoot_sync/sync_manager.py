"""Sync manager for transferring activities between Strava and Komoot."""

from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict
import json

from .api.strava_client import StravaClient
from .api.komoot_client import KomootClient


class SyncManager:
    """Manage syncing activities between Strava and Komoot."""
    
    def __init__(self, strava_client: StravaClient, komoot_client: KomootClient):
        """
        Initialize sync manager.
        
        Args:
            strava_client: Authenticated Strava client
            komoot_client: Authenticated Komoot client
        """
        self.strava = strava_client
        self.komoot = komoot_client
        self.sync_log: List[Dict] = []
        
    def sync_activity(self, activity_id: int, sport_override: Optional[str] = None) -> bool:
        """
        Sync a single activity from Strava to Komoot.
        
        Args:
            activity_id: Strava activity ID
            sport_override: Optional Komoot sport type override
            
        Returns:
            True if successful, False otherwise
        """
        print(f"\n📥 Syncing activity {activity_id}...")
        
        # Get activity details
        activity = self.strava.get_activity_details(activity_id)
        if not activity:
            print(f"✗ Failed to fetch activity details")
            return False
        
        activity_name = activity.get('name', f'Activity {activity_id}')
        activity_type = activity.get('type', 'Ride')
        
        print(f"   Activity: {activity_name}")
        print(f"   Type: {activity_type}")
        
        # Export GPX from Strava
        print(f"   Exporting GPX from Strava...")
        gpx_data = self.strava.export_activity_gpx(activity_id)
        
        if not gpx_data:
            print(f"✗ Failed to export GPX")
            return False
        
        # Determine Komoot sport type
        if sport_override:
            komoot_sport = sport_override
        else:
            komoot_sport = KomootClient.map_strava_to_komoot_sport(activity_type)
        
        print(f"   Komoot sport type: {komoot_sport}")
        
        # Upload to Komoot
        print(f"   Uploading to Komoot...")
        result = self.komoot.upload_gpx_data(gpx_data, activity_name, komoot_sport)
        
        if result:
            tour_id = result.get('id')
            print(f"✓ Successfully synced to Komoot (Tour ID: {tour_id})")
            
            # Log the sync
            self.sync_log.append({
                'timestamp': datetime.now().isoformat(),
                'strava_activity_id': activity_id,
                'strava_activity_name': activity_name,
                'strava_activity_type': activity_type,
                'komoot_tour_id': tour_id,
                'komoot_sport': komoot_sport,
                'status': 'success'
            })
            
            return True
        else:
            print(f"✗ Failed to upload to Komoot")
            
            # Log the failure
            self.sync_log.append({
                'timestamp': datetime.now().isoformat(),
                'strava_activity_id': activity_id,
                'strava_activity_name': activity_name,
                'strava_activity_type': activity_type,
                'status': 'failed'
            })
            
            return False
    
    def sync_activities(self, activity_ids: List[int], 
                       sport_override: Optional[str] = None) -> Dict[str, int]:
        """
        Sync multiple activities from Strava to Komoot.
        
        Args:
            activity_ids: List of Strava activity IDs
            sport_override: Optional Komoot sport type override for all activities
            
        Returns:
            Dictionary with success and failure counts
        """
        results = {'success': 0, 'failed': 0}
        
        print(f"\n🔄 Starting sync of {len(activity_ids)} activities...")
        
        for i, activity_id in enumerate(activity_ids, 1):
            print(f"\n[{i}/{len(activity_ids)}]", end=" ")
            
            if self.sync_activity(activity_id, sport_override):
                results['success'] += 1
            else:
                results['failed'] += 1
        
        print(f"\n\n📊 Sync Summary:")
        print(f"   ✓ Successful: {results['success']}")
        print(f"   ✗ Failed: {results['failed']}")
        
        return results
    
    def sync_date_range(self, after: Optional[datetime] = None,
                       before: Optional[datetime] = None,
                       activity_types: Optional[List[str]] = None,
                       sport_override: Optional[str] = None) -> Dict[str, int]:
        """
        Sync activities within a date range from Strava to Komoot.
        
        Args:
            after: Start date (inclusive)
            before: End date (inclusive)
            activity_types: Optional list of Strava activity types to sync
            sport_override: Optional Komoot sport type override
            
        Returns:
            Dictionary with success and failure counts
        """
        print(f"\n🔍 Fetching activities from Strava...")
        
        activities = self.strava.get_activities(after=after, before=before)
        
        if not activities:
            print("No activities found in the specified date range.")
            return {'success': 0, 'failed': 0}
        
        print(f"   Found {len(activities)} activities")
        
        # Filter by activity type if specified
        if activity_types:
            activities = [a for a in activities if a.get('type') in activity_types]
            print(f"   Filtered to {len(activities)} activities of types: {', '.join(activity_types)}")
        
        if not activities:
            print("No activities match the filter criteria.")
            return {'success': 0, 'failed': 0}
        
        # Extract activity IDs
        activity_ids = [a['id'] for a in activities]
        
        # Sync the activities
        return self.sync_activities(activity_ids, sport_override)
    
    def save_sync_log(self, output_path: Path):
        """
        Save sync log to a JSON file.
        
        Args:
            output_path: Path where to save the log
        """
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump(self.sync_log, f, indent=2)
            print(f"\n✓ Sync log saved to {output_path}")
        except IOError as e:
            print(f"\n✗ Error saving sync log: {e}")
    
    def load_sync_log(self, log_path: Path) -> bool:
        """
        Load sync log from a JSON file.
        
        Args:
            log_path: Path to the log file
            
        Returns:
            True if successful, False otherwise
        """
        if not log_path.exists():
            return False
        
        try:
            with open(log_path, 'r') as f:
                self.sync_log = json.load(f)
            return True
        except (json.JSONDecodeError, IOError) as e:
            print(f"✗ Error loading sync log: {e}")
            return False
    
    def get_synced_activity_ids(self) -> List[int]:
        """
        Get list of Strava activity IDs that have been successfully synced.
        
        Returns:
            List of activity IDs
        """
        return [
            entry['strava_activity_id']
            for entry in self.sync_log
            if entry.get('status') == 'success'
        ]
    
    def is_activity_synced(self, activity_id: int) -> bool:
        """
        Check if an activity has already been synced.
        
        Args:
            activity_id: Strava activity ID
            
        Returns:
            True if synced, False otherwise
        """
        return activity_id in self.get_synced_activity_ids()