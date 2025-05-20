#!/usr/bin/env python3

# <xbar.title>Bitbar Agenda</xbar.title>
# <xbar.version>v2.0</xbar.version>
# <xbar.author>Leo Herzog</xbar.author>
# <xbar.author.github>leoherzog</xbar.author.github>
# <xbar.desc>Displays upcoming meeting and list of meetings today from Google Calendar</xbar.desc>
# <xbar.dependencies>python,google-api-python-client,google-auth-oauthlib,humanize</xbar.dependencies>

from __future__ import annotations
import datetime
import os
import re
import humanize
import html
import json
import time
from sys import platform
from typing import Dict, List, Optional, Union, Any
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials


# Configuration
ids = [
  {
    'id': 'familycalendar@gmail.com',
    'icon': '👪'
  },
  {
    'id': 'workcalendar@example.com',
    'icon': '🏢'
  }
]
useColors = True
eventNamesToFilter = ['Work']
CACHE_FILE = 'calendar_cache.json'
CACHE_DURATION = 30  # seconds between API calls


def get_credentials() -> Credentials:
    """
    Get and refresh Google API credentials.
    Returns authenticated credentials object.
    """
    creds = None
    token_path = 'token.json'
    
    # Check if token file exists
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, ['https://www.googleapis.com/auth/calendar.readonly'])
    
    # If credentials don't exist or are invalid
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # Refresh existing credentials
            creds.refresh(Request())
        else:
            # Use InstalledAppFlow for compatibility
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json',
                ['https://www.googleapis.com/auth/calendar.readonly'])
            creds = flow.run_local_server(port=0)
            
        # Save credentials for next run
        with open(token_path, 'w') as token:
            token.write(creds.to_json())
    
    return creds


def findMeetingId(text: str) -> Optional[str]:
    """
    Find meeting URLs in text content.
    Returns the first match found or None.
    """
    if not text:
        return None
    
    # thanks https://github.com/leits/MeetingBar/blob/master/MeetingBar/Services/MeetingServices.swift
    meetingIdFormats = [
        # Google
        r"https?://meet\.google\.com/(_meet/)?[a-z-]+",
        r"https?://hangouts\.google\.com/[^\s]*",
        r"https?://stream\.meet\.google\.com/stream/[a-z0-9-]+",
        r"https?://duo\.app\.goo\.gl/[^\s]*",
        
        # Zoom
        r"https:\/\/(?:[a-zA-Z0-9-.]+)?zoom(-x)?\.(?:us|com|com\.cn|de)\/(?:my|[a-z]{1,2}|webinar)\/[-a-zA-Z0-9()@:%_\+.~#?&=\/]*",
        r"zoommtg://([a-z0-9-.]+)?zoom(-x)?\.(?:us|com|com\.cn|de)/join[-a-zA-Z0-9()@:%_\+.~#?&=\/]*",
        r"https?://([a-z0-9.]+)?zoomgov\.com/j/[a-zA-Z0-9?&=]+",
        r"https://welink\.zhumu\.com/j/[0-9]+?pwd=[a-zA-Z0-9]+",
        r"https://([a-zA-Z0-9.]+)\.zm\.page",
        
        # Microsoft
        r"https?://(gov.)?teams\.microsoft\.(com|us)/l/meetup-join/[a-zA-Z0-9_%\/=\-\+\.?]+",
        r"https?://meet\.lync\.com/[^\s]*",
        r"https?:\/\/(meet|join)\.[^\s]*\/[a-z0-9.]+/meet\/[A-Za-z0-9./]+",

        r"https?://(?:[A-Za-z0-9-]+\.)?webex\.com(?:(?:/[-A-Za-z0-9]+/j\.php\?MTID=[A-Za-z0-9]+(?:&\S*)?)|(?:/(?:meet|join)/[A-Za-z0-9\-._@]+(?:\?\S*)?))",
        r"https?://meet\.jit\.si/[^\s]*",
        r"https?://([a-z0-9-.]+)?chime\.aws/[0-9]*",
        r"https?://([a-z0-9.]+)?ringcentral\.com/[^\s]*",
        r"https?://meetings\.ringcentral\.com/[^\s]*",
        r"https?://([a-z0-9.]+)?gotomeeting\.com/[^\s]*",
        r"https?://([a-z0-9.]+)?gotowebinar\.com/[^\s]*",
        r"https?://([a-z0-9.]+)?bluejeans\.com/[^\s]*",
        r"https?://join\.skype\.com/[^\s]*",
        r"https?://8x8\.vc/[^\s]*",
        r"https?://event\.demio\.com/[^\s]*",
        r"https?://join\.me/[^\s]*",
        r"https?://whereby\.com/[^\s]*",
        r"https?://uberconference\.com/[^\s]*",
        r"https?://go\.blizz\.com/[^\s]*",
        r"https?://go\.teamviewer\.com/[^\s]*",
        r"https?://vsee\.com/[^\s]*",
        r"https?://meet\.starleaf\.com/[^\s]*",
        r"https?://voovmeeting\.com/[^\s]*",
        r"https?://([a-z0-9-.]+)?workplace\.com/groupcall/[^\s]+",
        r"https?://call\.lifesizecloud\.com/[^\s]*",
        r"https?://meetings\.vonage\.com/[0-9]{9}",
        r"https?://(meet\.)?around\.co/[^\s]*",
        r"https?://jam\.systems/[^\s]*",
        r"https?://us\.bbcollab\.com/[^\s]*",
        r"https?://join\.coscreen\.co/[^\s]*",
        r"https?://([a-z0-9.]+)?vowel\.com/#/g/[^\s]*",
        r"https://vc\.larksuite\.com/j/[0-9]+",
        r"https://vc\.feishu\.cn/j/[0-9]+",
        r"https://vimeo\.com/(showcase|event)/[0-9]+|https://venues\.vimeo\.com/[^\s]+",
        r"https://([a-z0-9-.]+)?ovice\.in/[^\s]*",
        r"https://facetime\.apple\.com/join[^\s]*",
        r"https?://go\.chorus\.ai/[^\s]+",
        r"https?://pop\.com/j/[0-9-]+",
        r"https?://([a-z0-9-.]+)?join\.gong\.io/[^\s]+",
        r"https?://app\.livestorm\.com/p/[^\s]+",
        r"https://lu\.ma/join/[^\s]*",
        r"https://preply\.com/[^\s]*",
        r"https://go\.userzoom\.com/participate/[a-z0-9-]+",
        r"https://app\.venue\.live/app/[^\s]*",
        r"https://app\.teemyco\.com/room/[^\s]*",
        r"https://demodesk\.com/[^\s]*",
        r"https://cliq\.zoho\.eu/meetings/[^\s]*",
        r"https?://app\.slack\.com/huddle/[A-Za-z0-9./]+",
        r"https?://reclaim\.ai/z/[A-Za-z0-9./]+",
        r"https://tuple\.app/c/[^\s]*",
        r"https?://app.gather.town/app/[A-Za-z0-9]+/[A-Za-z0-9_%\-]+\?(spawnToken|meeting)=[^\s]*",
        r"https?://meet\.pumble\.com/[a-z-]+",
        r"https?://([a-z0-9.]+)?conference\.istesuit\.com/[^\s]*+",
        r"https?://([a-z0-9.]+)?doxy\.me/[^\s]*",
        r"https?://app.cal\.com/video/[A-Za-z0-9./]+",
        r"https?://meet[a-zA-Z0-9.]*\.livekit\.io/rooms/[a-zA-Z0-9-#]+",
        r"https?://meetings\.conf\.meetecho\.com/.+",
        
        # Discord and streaming
        r"(https|discord)://(www\.)?(canary\.)?discord(app)?\.([a-zA-Z]{2,})(.+)?",
        r"https?://((www|m)\.)?(youtube\.com|youtu\.be)/[^\s]*"
    ]

    for urlFormat in meetingIdFormats:
        match = re.search(urlFormat, text, re.IGNORECASE)
        if match:
            return match.group(0)
    return None


def format_time_until(now: datetime.datetime, start: datetime.datetime) -> str:
    """Format time until an event using natural language from humanize"""
    time_diff = start - now
    
    if time_diff.total_seconds() > 0:
        return humanize.naturaldelta(time_diff)
    else:
        return humanize.naturaldelta(-time_diff) + " ago"


def read_cache() -> tuple[List[Dict[str, Any]], float]:
    """Read event data from cache file"""
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r') as f:
                cache_data = json.load(f)
                return cache_data['events'], cache_data['timestamp']
    except Exception as e:
        print(f"Error reading cache: {e}")
    return [], 0


def write_cache(events: List[Dict[str, Any]]):
    """Write event data to cache file"""
    try:
        cache_data = {
            'events': events,
            'timestamp': time.time()
        }
        with open(CACHE_FILE, 'w') as f:
            json.dump(cache_data, f)
    except Exception as e:
        print(f"Error writing cache: {e}")


def fetch_events(service) -> List[Dict[str, Any]]:
    """Fetch events from Google Calendar API"""
    now = datetime.datetime.now().astimezone()
    beginningOfDay = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    endOfDay = now.replace(hour=23, minute=59, second=59, microsecond=0).isoformat()

    # Get color definitions
    colors = service.colors().get().execute()

    # Collect events from all calendars
    events: List[Dict[str, Any]] = []
    for cal in ids:
        try:
            thisCalInList = service.calendarList().get(calendarId=cal['id']).execute()
            thisCalsEvents = service.events().list(
                calendarId=cal['id'], 
                timeMin=beginningOfDay, 
                timeMax=endOfDay, 
                maxResults=50, 
                maxAttendees=1, 
                singleEvents=True
            ).execute().get('items', [])
            
            for event in thisCalsEvents:
                # Process event summary - escape HTML and replace pipe character
                event['summary'] = html.escape(event.get('summary', '')).replace('|', '∣')
                event['icon'] = cal['icon']
                
                # Set color based on event or calendar
                if event.get('colorId'):
                    event['color'] = colors.get('event', {}).get(event.get('colorId'), {}).get('background')
                elif thisCalInList.get('backgroundColor'):
                    event['color'] = thisCalInList.get('backgroundColor')
                else:
                    event['color'] = colors.get('calendar', {}).get(thisCalInList.get('colorId'), {}).get('background')
            
            events.extend(thisCalsEvents)
        except Exception as e:
            print(f"Error retrieving calendar {cal['id']}: {e}")
            print("---")
            return []

    # Filter events
    # Remove events in filter list
    events = [x for x in events if x.get('summary') not in eventNamesToFilter]
    
    # Remove declined events
    events = [x for x in events if not x.get('attendees') or x.get('attendees')[0].get('responseStatus', '') != 'declined']
    
    # Sort events by start time
    events.sort(key=lambda event: event['start'].get('dateTime', event['start'].get('date')))
    
    return events


def display_events(events: List[Dict[str, Any]]):
    """Display events in xbar/Argos format"""
    now = datetime.datetime.now().astimezone()
    
    # Display next upcoming meeting
    found_next_event = False
    for event in events:
        # Skip all-day events
        if not event['start'].get('dateTime'):
            continue

        start = datetime.datetime.fromisoformat(event['start'].get('dateTime').replace('Z', '+00:00'))
        window = start + datetime.timedelta(minutes=5)

        if now < window:
            nextEvent = event.get('summary')
            if len(nextEvent) > 24:
                nextEvent = nextEvent[:24] + '…'
                
            if start > now:
                print(f"{nextEvent} in {format_time_until(now, start)}")
            elif start < now:
                print(f"⚠️ {nextEvent} started {format_time_until(now, start)}")
            else:
                print(f"{nextEvent} starting now")
                
            found_next_event = True
            break
    
    # If we didn't find any upcoming events
    if not found_next_event and events:
        print("No Upcoming Events")
    elif not events:
        print("No Events Today")

    print("---")

    # List all events for today
    if not events:
        print("No events today")
    
    for event in events:
        row = event.get('summary', '')
        
        # Add time if not all-day
        start = event.get('start', {}).get('dateTime')
        if start:
            start_time = datetime.datetime.fromisoformat(start.replace('Z', '+00:00'))
            row = f"{start_time.strftime('%-I:%M%p')} {row}"
        
        # Add strikethrough if event has ended
        end = event.get('end', {}).get('dateTime')
        if end:
            end_time = datetime.datetime.fromisoformat(end.replace('Z', '+00:00'))
            if end_time < now:
                striketext = ''.join([f"{letter}\u0336" for letter in row])
                striketext = striketext.replace('&\u0336a\u0336m\u0336p\u0336;\u0336', '&amp;')  # Don't strikethrough &amp;
                row = striketext
        
        # Find meeting URL
        meetingUrl = None
        
        # First check conferenceData (most reliable source)
        attachedMeetingUrl = event.get('conferenceData', {}).get('entryPoints', [])
        if attachedMeetingUrl:
            # Look for video entry points first
            video_entries = [x for x in attachedMeetingUrl if x.get('entryPointType') == 'video']
            if video_entries:
                meetingUrl = video_entries[0].get('uri')
        
        # If no conferenceData, look in location and description
        if not meetingUrl:
            meetingUrl = findMeetingId(event.get('location', '')) or findMeetingId(event.get('description', ''))
        
        # Add meeting link or spacer
        if meetingUrl:
            row += f" ↗ | href={meetingUrl} "
        else:
            row += " | "

        # Add color if available
        if useColors and event.get('color'):
            row += f"color={event.get('color')} "

        # Add icon if available 
        if event.get('icon'):
            row = f"{event.get('icon')} {row}"

        print(row)


def main() -> None:
    """Main function to display calendar events"""
    # Set working directory based on platform
    if platform == "darwin":
        os.chdir(os.path.expanduser('~') + '/Library/Application Support/xbar/plugins')
    elif platform == "linux" or platform == "linux2":
        os.chdir(os.path.expanduser('~') + '/.config/argos/')

    # Check if we need to fetch from API or use cache
    cached_events, timestamp = read_cache()
    current_time = time.time()
    
    # Decide whether to use cache or fetch fresh data
    if not cached_events or (current_time - timestamp) > CACHE_DURATION:
        # Cache expired or doesn't exist, fetch fresh data
        creds = get_credentials()
        service = build('calendar', 'v3', credentials=creds)
        events = fetch_events(service)
        
        # Cache the events for future runs
        if events:
            write_cache(events)
    else:
        # Use cached events
        events = cached_events
    
    # Display events (using current time for time-based formatting)
    display_events(events)


if __name__ == '__main__':
    main()