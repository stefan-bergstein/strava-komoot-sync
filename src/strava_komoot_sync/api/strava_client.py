"""Strava API client for authentication and activity management."""

import requests
from datetime import datetime
from typing import Optional, List, Dict, BinaryIO
from pathlib import Path
import gpxpy  # type: ignore
import gpxpy.gpx  # type: ignore


class StravaClient:
    """Handle Strava API authentication and activity operations."""
    
    BASE_URL = "https://www.strava.com/api/v3"
    AUTH_URL = "https://www.strava.com/oauth/token"
    
    def __init__(self, client_id: str, client_secret: str, refresh_token: str):
        """
        Initialize Strava client with API credentials.
        
        Args:
            client_id: Strava application client ID
            client_secret: Strava application client secret
            refresh_token: OAuth refresh token for authentication
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[int] = None
        
    def authenticate(self) -> bool:
        """
        Get a fresh access token using the refresh token.
        
        Returns:
            True if authentication successful, False otherwise
        """
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
            
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"✗ Strava authentication failed: {e}")
            return False
    
    def _ensure_authenticated(self):
        """Ensure we have a valid access token."""
        if not self.access_token or (self.token_expires_at is not None and 
                                     datetime.now().timestamp() >= self.token_expires_at):
            if not self.authenticate():
                raise Exception("Failed to authenticate with Strava API")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get authorization headers for API requests."""
        self._ensure_authenticated()
        return {'Authorization': f'Bearer {self.access_token}'}
    
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
        params = {'per_page': per_page, 'page': 1}
        
        if after:
            params['after'] = int(after.timestamp())
        if before:
            params['before'] = int(before.timestamp())
        
        all_activities = []
        
        while True:
            try:
                response = requests.get(
                    f"{self.BASE_URL}/athlete/activities",
                    headers=self._get_headers(),
                    params=params
                )
                response.raise_for_status()
                activities = response.json()
                
                if not activities:
                    break
                
                all_activities.extend(activities)
                params['page'] += 1
                
            except requests.exceptions.RequestException as e:
                print(f"✗ Error fetching activities: {e}")
                break
        
        return all_activities
    
    def get_activity_details(self, activity_id: int) -> Optional[Dict]:
        """
        Fetch detailed information for a specific activity.
        
        Args:
            activity_id: The Strava activity ID
            
        Returns:
            Detailed activity dictionary or None if failed
        """
        try:
            response = requests.get(
                f"{self.BASE_URL}/activities/{activity_id}",
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"✗ Error fetching activity {activity_id}: {e}")
            return None
    
    def get_activity_streams(self, activity_id: int, 
                           stream_types: Optional[List[str]] = None) -> Optional[Dict]:
        """
        Fetch activity streams (GPS data, heart rate, etc.).
        
        Args:
            activity_id: The Strava activity ID
            stream_types: List of stream types to fetch (e.g., ['latlng', 'time', 'altitude'])
                         If None, fetches all available streams
            
        Returns:
            Dictionary of stream data or None if failed
        """
        if stream_types is None:
            stream_types = ['time', 'latlng', 'distance', 'altitude', 'velocity_smooth',
                          'heartrate', 'cadence', 'watts', 'temp', 'moving', 'grade_smooth']
        
        keys = ','.join(stream_types)
        
        try:
            response = requests.get(
                f"{self.BASE_URL}/activities/{activity_id}/streams",
                headers=self._get_headers(),
                params={'keys': keys, 'key_by_type': True}
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"✗ Error fetching streams for activity {activity_id}: {e}")
            return None
    
    def export_activity_gpx(self, activity_id: int) -> Optional[bytes]:
        """
        Export activity as GPX file.
        First tries the official export endpoint, then falls back to generating from streams.
        
        Args:
            activity_id: The Strava activity ID
            
        Returns:
            GPX file content as bytes or None if failed
        """
        try:
            # Try official GPX export endpoint first
            response = requests.get(
                f"{self.BASE_URL}/activities/{activity_id}/export_gpx",
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.content
            
        except requests.exceptions.RequestException:
            # If export fails (404 or other error), try generating from streams
            # This is normal for many activities - Strava's export endpoint is limited
            print(f"   Using activity streams to generate GPX...")
            return self._generate_gpx_from_streams(activity_id)
    
    def _generate_gpx_from_streams(self, activity_id: int) -> Optional[bytes]:
        """
        Generate GPX file from activity streams.
        
        Args:
            activity_id: The Strava activity ID
            
        Returns:
            GPX file content as bytes or None if failed
        """
        try:
            # Get activity details for metadata
            activity = self.get_activity_details(activity_id)
            if not activity:
                return None
            
            # Get activity streams
            streams = self.get_activity_streams(activity_id, ['time', 'latlng', 'altitude'])
            if not streams or 'latlng' not in streams:
                print(f"   No GPS data available for activity {activity_id}")
                return None
            
            # Create GPX object
            gpx = gpxpy.gpx.GPX()
            
            # Create track
            gpx_track = gpxpy.gpx.GPXTrack()
            gpx_track.name = activity.get('name', f'Activity {activity_id}')
            gpx_track.type = activity.get('type', 'Ride')
            gpx.tracks.append(gpx_track)
            
            # Create segment
            gpx_segment = gpxpy.gpx.GPXTrackSegment()
            gpx_track.segments.append(gpx_segment)
            
            # Get data arrays
            latlng_data = streams['latlng']['data']
            time_data = streams.get('time', {}).get('data', [])
            altitude_data = streams.get('altitude', {}).get('data', [])
            
            # Parse start time
            start_time = datetime.fromisoformat(activity['start_date'].replace('Z', '+00:00'))
            
            # Add track points
            for i, (lat, lng) in enumerate(latlng_data):
                # Calculate time for this point
                if i < len(time_data):
                    point_time = start_time.timestamp() + time_data[i]
                    point_datetime = datetime.fromtimestamp(point_time)
                else:
                    point_datetime = None
                
                # Get elevation if available
                elevation = altitude_data[i] if i < len(altitude_data) else None
                
                # Create track point
                track_point = gpxpy.gpx.GPXTrackPoint(
                    latitude=lat,
                    longitude=lng,
                    elevation=elevation,
                    time=point_datetime
                )
                gpx_segment.points.append(track_point)
            
            # Convert to XML bytes
            gpx_xml = gpx.to_xml()
            return gpx_xml.encode('utf-8')
            
        except Exception as e:
            print(f"✗ Error generating GPX from streams: {e}")
            return None
    
    def save_activity_gpx(self, activity_id: int, output_path: Path) -> bool:
        """
        Export and save activity as GPX file.
        
        Args:
            activity_id: The Strava activity ID
            output_path: Path where to save the GPX file
            
        Returns:
            True if successful, False otherwise
        """
        gpx_data = self.export_activity_gpx(activity_id)
        
        if gpx_data:
            try:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'wb') as f:
                    f.write(gpx_data)
                return True
            except IOError as e:
                print(f"✗ Error saving GPX file: {e}")
                return False
        
        return False
    
    def get_athlete(self) -> Optional[Dict]:
        """
        Get authenticated athlete information.
        
        Returns:
            Athlete data dictionary or None if failed
        """
        try:
            response = requests.get(
                f"{self.BASE_URL}/athlete",
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"✗ Error fetching athlete data: {e}")
            return None