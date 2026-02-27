"""Komoot API client using kompy library for tour management and GPX imports."""

from typing import Optional, List, Dict
from pathlib import Path
from kompy import KomootConnector  # type: ignore
import tempfile
import gpxpy  # type: ignore


class KomootClient:
    """Handle Komoot API authentication and tour operations using kompy."""
    
    def __init__(self, email: str, password: str):
        """
        Initialize Komoot client with credentials.
        
        Args:
            email: Komoot account email
            password: Komoot account password
        """
        self.email = email
        self.password = password
        self.connector: Optional[KomootConnector] = None
        self._authenticated = False
        
    def authenticate(self) -> bool:
        """
        Authenticate with Komoot API using kompy.
        
        Returns:
            True if authentication successful, False otherwise
        """
        try:
            self.connector = KomootConnector(
                email=self.email,
                password=self.password
            )
            self._authenticated = True
            # Test the connection by trying to get tours
            _ = self.connector.get_tours()  # type: ignore
            print(f"✓ Authenticated with Komoot as: {self.email}")
            return True
            
        except Exception as e:
            print(f"✗ Komoot authentication failed: {e}")
            return False
    
    def _ensure_authenticated(self):
        """Ensure we are authenticated."""
        if not self._authenticated or self.connector is None:
            if not self.authenticate():
                raise Exception("Failed to authenticate with Komoot API")
    
    def get_user_profile(self) -> Optional[Dict]:
        """
        Get user profile information.
        
        Returns:
            User profile dictionary or None if failed
        """
        self._ensure_authenticated()
        
        try:
            # Return basic profile info
            return {
                'email': self.email,
                'authenticated': True
            }
        except Exception as e:
            print(f"✗ Error fetching Komoot profile: {e}")
            return None
    
    def get_tours(self, tour_type: str = "tour_recorded") -> Optional[List[Dict]]:
        """
        Get user's tours.
        
        Args:
            tour_type: Type of tours to fetch ('tour_recorded', 'tour_planned', etc.)
            
        Returns:
            List of tour dictionaries or None if failed
        """
        self._ensure_authenticated()
        
        try:
            # Get tours from kompy
            tours = self.connector.get_tours()  # type: ignore
            
            # Convert to list of dicts if needed
            if tours:
                return [tour for tour in tours]
            return []
            
        except Exception as e:
            print(f"✗ Error fetching Komoot tours: {e}")
            return None
    
    def upload_gpx(self, gpx_file: Path, name: Optional[str] = None,
                   sport: str = "touringbicycle") -> Optional[Dict]:
        """
        Upload a GPX file to Komoot.
        
        Args:
            gpx_file: Path to GPX file
            name: Optional name for the tour (uses filename if not provided)
            sport: Sport type (e.g., 'touringbicycle', 'mtb', 'racebike', 'jogging', 'hiking')
            
        Returns:
            Created tour dictionary or None if failed
        """
        self._ensure_authenticated()
        
        if not gpx_file.exists():
            print(f"✗ GPX file not found: {gpx_file}")
            return None
        
        if name is None:
            name = gpx_file.stem
        
        try:
            # Parse GPX file
            with open(gpx_file, 'r') as f:
                gpx = gpxpy.parse(f)
            
            # Use kompy to upload the tour
            success = self.connector.upload_tour(  # type: ignore
                tour_object=gpx,
                activity_type=sport,
                tour_name=name
            )
            
            if success:
                return {
                    'name': name,
                    'sport': sport,
                    'status': 'success'
                }
            return None
                
        except Exception as e:
            print(f"✗ Error uploading GPX to Komoot: {e}")
            return None
    
    def upload_gpx_data(self, gpx_data: bytes, name: str,
                       sport: str = "touringbicycle") -> Optional[Dict]:
        """
        Upload GPX data directly to Komoot.
        
        Args:
            gpx_data: GPX file content as bytes
            name: Name for the tour
            sport: Sport type
            
        Returns:
            Created tour dictionary or None if failed
        """
        self._ensure_authenticated()
        
        try:
            # Parse GPX data
            gpx = gpxpy.parse(gpx_data.decode('utf-8'))
            
            # Use kompy to upload the tour
            success = self.connector.upload_tour(  # type: ignore
                tour_object=gpx,
                activity_type=sport,
                tour_name=name
            )
            
            if success:
                return {
                    'name': name,
                    'sport': sport,
                    'status': 'success'
                }
            return None
            
        except Exception as e:
            print(f"✗ Error uploading GPX data to Komoot: {e}")
            return None
    
    def get_tour_details(self, tour_id: str) -> Optional[Dict]:
        """
        Get detailed information about a tour.
        
        Args:
            tour_id: Komoot tour ID
            
        Returns:
            Tour details dictionary or None if failed
        """
        self._ensure_authenticated()
        
        try:
            tour = self.connector.get_tour_by_id(tour_id)  # type: ignore
            if tour:
                return {
                    'id': tour.id if hasattr(tour, 'id') else tour_id,
                    'name': tour.name if hasattr(tour, 'name') else 'Unknown',
                    'sport': tour.sport if hasattr(tour, 'sport') else 'Unknown'
                }
            return None
            
        except Exception as e:
            print(f"✗ Error fetching tour {tour_id}: {e}")
            return None
    
    def delete_tour(self, tour_id: str) -> bool:
        """
        Delete a tour from Komoot.
        
        Args:
            tour_id: Komoot tour ID
            
        Returns:
            True if successful, False otherwise
        """
        self._ensure_authenticated()
        
        try:
            self.connector.delete_tour(tour_id)  # type: ignore
            return True
            
        except Exception as e:
            print(f"✗ Error deleting tour {tour_id}: {e}")
            return False
    
    @staticmethod
    def map_strava_to_komoot_sport(strava_type: str) -> str:
        """
        Map Strava activity type to Komoot sport type.
        
        Args:
            strava_type: Strava activity type
            
        Returns:
            Corresponding Komoot sport type
        """
        mapping = {
            'Ride': 'touringbicycle',
            'VirtualRide': 'touringbicycle',
            'EBikeRide': 'e_touringbicycle',
            'MountainBikeRide': 'mtb',
            'GravelRide': 'mtb',
            'Run': 'jogging',
            'TrailRun': 'jogging',
            'Walk': 'hiking',
            'Hike': 'hiking',
            'RoadBike': 'racebike',
        }
        
        return mapping.get(strava_type, 'touringbicycle')