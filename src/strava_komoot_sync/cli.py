#!/usr/bin/env python3
"""Command-line interface for Strava to Komoot sync tool."""

import argparse
import sys
from datetime import datetime
from pathlib import Path

from .api.strava_client import StravaClient
from .api.komoot_client import KomootClient
from .sync_manager import SyncManager
from .utils.config import Config


def parse_date(date_str: str) -> datetime:
    """Parse date string in YYYY-MM-DD format."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid date format: {date_str}. Use YYYY-MM-DD")


def cmd_download(args, config: Config):
    """Download activities from Strava."""
    if not config.validate_strava_config():
        return 1
    
    # Initialize Strava client
    strava = StravaClient(
        client_id=config.get('strava.client_id'),
        client_secret=config.get('strava.client_secret'),
        refresh_token=config.get('strava.refresh_token')
    )
    
    if not strava.authenticate():
        return 1
    
    print(f"✓ Authenticated with Strava")
    
    # Fetch activities
    print(f"\n🔍 Fetching activities...")
    activities = strava.get_activities(after=args.after, before=args.before)
    
    if not activities:
        print("No activities found.")
        return 0
    
    print(f"✓ Found {len(activities)} activities")
    
    # Save activities
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save summary
    import json
    summary_file = output_dir / "activities_summary.json"
    with open(summary_file, 'w') as f:
        json.dump(activities, f, indent=2)
    print(f"✓ Saved summary to {summary_file}")
    
    # Export GPX files if requested
    if args.export_gpx:
        gpx_dir = output_dir / "gpx"
        gpx_dir.mkdir(exist_ok=True)
        
        print(f"\n📥 Exporting GPX files...")
        for i, activity in enumerate(activities, 1):
            activity_id = activity['id']
            activity_date = activity['start_date'][:10]
            activity_type = activity['type'].lower().replace(' ', '_')
            
            gpx_file = gpx_dir / f"{activity_date}_{activity_type}_{activity_id}.gpx"
            
            print(f"  [{i}/{len(activities)}] Exporting {activity_id}...", end=" ")
            
            if strava.save_activity_gpx(activity_id, gpx_file):
                print("✓")
            else:
                print("✗")
        
        print(f"✓ GPX files saved to {gpx_dir}")
    
    return 0


def cmd_sync(args, config: Config):
    """Sync activities from Strava to Komoot."""
    if not config.validate_strava_config():
        return 1
    
    if not config.validate_komoot_config():
        return 1
    
    # Initialize clients
    strava = StravaClient(
        client_id=config.get('strava.client_id'),
        client_secret=config.get('strava.client_secret'),
        refresh_token=config.get('strava.refresh_token')
    )
    
    komoot = KomootClient(
        email=config.get('komoot.email'),
        password=config.get('komoot.password')
    )
    
    # Authenticate
    if not strava.authenticate():
        return 1
    print(f"✓ Authenticated with Strava")
    
    if not komoot.authenticate():
        return 1
    print(f"✓ Authenticated with Komoot")
    
    # Initialize sync manager
    sync_manager = SyncManager(strava, komoot)
    
    # Load existing sync log if available
    log_file = Path(args.log_file)
    if log_file.exists():
        sync_manager.load_sync_log(log_file)
        print(f"✓ Loaded sync log ({len(sync_manager.sync_log)} entries)")
    
    # Sync activities
    if args.activity_ids:
        # Sync specific activities
        activity_ids = [int(id) for id in args.activity_ids.split(',')]
        results = sync_manager.sync_activities(activity_ids, args.sport)
    else:
        # Sync by date range
        activity_types = args.types.split(',') if args.types else None
        results = sync_manager.sync_date_range(
            after=args.after,
            before=args.before,
            activity_types=activity_types,
            sport_override=args.sport
        )
    
    # Save sync log
    sync_manager.save_sync_log(log_file)
    
    return 0 if results['failed'] == 0 else 1


def cmd_list(args, config: Config):
    """List activities from Strava or Komoot."""
    if args.source == 'strava':
        if not config.validate_strava_config():
            return 1
        
        strava = StravaClient(
            client_id=config.get('strava.client_id'),
            client_secret=config.get('strava.client_secret'),
            refresh_token=config.get('strava.refresh_token')
        )
        
        if not strava.authenticate():
            return 1
        
        print(f"✓ Authenticated with Strava\n")
        
        activities = strava.get_activities(after=args.after, before=args.before)
        
        if not activities:
            print("No activities found.")
            return 0
        
        print(f"Found {len(activities)} activities:\n")
        print(f"{'ID':<12} {'Date':<12} {'Type':<20} {'Name':<40}")
        print("-" * 90)
        
        for activity in activities:
            activity_id = activity['id']
            date = activity['start_date'][:10]
            activity_type = activity['type']
            name = activity['name'][:37] + "..." if len(activity['name']) > 40 else activity['name']
            
            print(f"{activity_id:<12} {date:<12} {activity_type:<20} {name:<40}")
    
    elif args.source == 'komoot':
        if not config.validate_komoot_config():
            return 1
        
        komoot = KomootClient(
            email=config.get('komoot.email'),
            password=config.get('komoot.password')
        )
        
        if not komoot.authenticate():
            return 1
        
        print(f"✓ Authenticated with Komoot\n")
        
        tours = komoot.get_tours()
        
        if not tours:
            print("No tours found.")
            return 0
        
        print(f"Found {len(tours)} tours:\n")
        print(f"{'ID':<12} {'Date':<12} {'Type':<20} {'Name':<40}")
        print("-" * 90)
        
        for tour in tours:
            # Tour objects have attributes, not dictionary keys
            tour_id = str(tour.id) if hasattr(tour, 'id') else 'N/A'  # type: ignore
            date = str(tour.date)[:10] if hasattr(tour, 'date') and tour.date else 'N/A'  # type: ignore
            tour_type = str(tour.sport) if hasattr(tour, 'sport') else 'N/A'  # type: ignore
            name = str(tour.name) if hasattr(tour, 'name') else 'Unnamed'  # type: ignore
            
            # Truncate long names
            if len(name) > 40:
                name = name[:37] + "..."
            
            print(f"{tour_id:<12} {date:<12} {tour_type:<20} {name:<40}")
    
    return 0


def cmd_config(args):
    """Manage configuration."""
    config_path = Path(args.config_file)
    
    if args.init:
        Config.create_example_config(config_path)
        return 0
    
    return 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Strava to Komoot Activity Sync Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--config',
        dest='config_file',
        default='config.json',
        help='Path to configuration file (default: config.json)'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Download command
    download_parser = subparsers.add_parser('download', help='Download activities from Strava')
    download_parser.add_argument('--after', type=parse_date, help='Download activities after this date (YYYY-MM-DD)')
    download_parser.add_argument('--before', type=parse_date, help='Download activities before this date (YYYY-MM-DD)')
    download_parser.add_argument('--output', default='./strava_data', help='Output directory (default: ./strava_data)')
    download_parser.add_argument('--export-gpx', action='store_true', help='Export activities as GPX files')
    
    # Sync command
    sync_parser = subparsers.add_parser('sync', help='Sync activities from Strava to Komoot')
    sync_parser.add_argument('--after', type=parse_date, help='Sync activities after this date (YYYY-MM-DD)')
    sync_parser.add_argument('--before', type=parse_date, help='Sync activities before this date (YYYY-MM-DD)')
    sync_parser.add_argument('--activity-ids', help='Comma-separated list of Strava activity IDs to sync')
    sync_parser.add_argument('--types', help='Comma-separated list of activity types to sync (e.g., Ride,Run)')
    sync_parser.add_argument('--sport', help='Override Komoot sport type for all activities')
    sync_parser.add_argument('--log-file', default='sync_log.json', help='Path to sync log file (default: sync_log.json)')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List activities from Strava or Komoot')
    list_parser.add_argument('source', choices=['strava', 'komoot'], help='Source to list from')
    list_parser.add_argument('--after', type=parse_date, help='List activities after this date (YYYY-MM-DD)')
    list_parser.add_argument('--before', type=parse_date, help='List activities before this date (YYYY-MM-DD)')
    
    # Config command
    config_parser = subparsers.add_parser('config', help='Manage configuration')
    config_parser.add_argument('--init', action='store_true', help='Create example configuration file')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Execute command
    if args.command == 'config':
        return cmd_config(args)
    
    # Load configuration for other commands
    config = Config(Path(args.config_file))
    if not config.load():
        print(f"\nRun 'python -m strava_komoot_sync.cli config --init' to create an example config file.")
        return 1
    
    if args.command == 'download':
        return cmd_download(args, config)
    elif args.command == 'sync':
        return cmd_sync(args, config)
    elif args.command == 'list':
        return cmd_list(args, config)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())