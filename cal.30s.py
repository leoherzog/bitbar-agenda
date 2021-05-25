#!/usr/bin/env python3

# <xbar.title>Bitbar Agenda</xbar.title>
# <xbar.version>v1.0</xbar.version>
# <xbar.author>Leo Herzog</xbar.author>
# <xbar.author.github>leoherzog</xbar.author.github>
# <xbar.desc>Displays upcoming meeting and list of meetings today from Google Calendar</xbar.desc>
# <xbar.dependencies>python,googleapiclient,humanize</xbar.dependencies>


import datetime
import os
import re
import humanize
import html
from sys import platform
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials


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


def main():

  if platform == "darwin":
    os.chdir(os.path.expanduser('~') + '/Library/Application Support/xbar/plugins')
  elif platform == "linux" or platform == "linux2":
    os.chdir(os.path.expanduser('~') + '/.config/argos/')

  creds = None
  
  if os.path.exists('token.json'):
    creds = Credentials.from_authorized_user_file('token.json', ['https://www.googleapis.com/auth/calendar.readonly'])
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file('credentials.json', ['https://www.googleapis.com/auth/calendar.readonly'])
      creds = flow.run_local_server(port=0)
    with open('token.json', 'w') as token:
      token.write(creds.to_json()) # Save the credentials for the next run

  service = build('calendar', 'v3', credentials=creds)

  beginningOfDay = datetime.datetime.now().astimezone().replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
  endOfDay = datetime.datetime.now().astimezone().replace(hour=23, minute=59, second=59, microsecond=0).isoformat()

  colors = service.colors().get().execute() # pylint: disable=no-member

  events = []
  for cal in ids:
    thisCalInList = service.calendarList().get(calendarId=cal['id']).execute() # pylint: disable=no-member
    thisCalsEvents = service.events().list(calendarId=cal['id'], timeMin=beginningOfDay, timeMax=endOfDay, maxResults=50, maxAttendees=1, singleEvents=True).execute().get('items', []) # pylint: disable=no-member
    for event in thisCalsEvents:
      event['summary'] = html.escape(event.get('summary', '')).replace('|', '∣') # reserved character for bitbar/argos. replace "vertical bar" with "divides" unicode character.
      event['icon'] = cal['icon']
      if event.get('colorId'): # look up colorId if set on event itself
        event['color'] = colors.get('event', {}).get(event.get('colorId'), {}).get('background')
      elif thisCalInList.get('backgroundColor'): # check for custom color on calendar
        event['color'] = thisCalInList.get('backgroundColor')
      else: # look up colorId for calendar
        event['color'] = colors.get('calendar', {}).get(thisCalInList.get('colorId')).get('background')
    events = events + thisCalsEvents

  # remove names in the filter
  events = [x for x in events if not x.get('summary') in eventNamesToFilter]
  
  # remove events that have been declined, if attendees key exists
  events = [x for x in events if not x.get('attendees') or x.get('attendees')[0].get('responseStatus', '') != 'declined']
  
  # sort by start time
  events.sort(key = lambda event : event['start'].get('dateTime', event['start'].get('date')))

  now = datetime.datetime.now().astimezone()

  # print next meeting first
  for event in events:

    if not event['start'].get('dateTime'): # all-day
      continue

    start = datetime.datetime.strptime(event['start'].get('dateTime'), '%Y-%m-%dT%H:%M:%S%z')
    window = start + datetime.timedelta(minutes=5)

    if now < window:
      nextEvent = event.get('summary')
      if len(nextEvent) > 24:
        nextEvent = nextEvent[:24] + '…'
      if start > now:
        print(nextEvent + ' in ' + humanize.naturaldelta(now - start))
      elif start < now:
        print('⚠️ ' + nextEvent + ' started ' + humanize.naturaldelta(now - start) + ' ago')
      else:
        print(nextEvent + ' starting now')
      break
    
    # if this is last in list and didn't break out of loop yet, must be no more today
    if event == events[-1]:
      print('No Upcoming Events')

  print('---')

  # then list all today

  if not events:
    print('No events today')
  
  for event in events:

    row = event.get('summary')
    
    # add time if not all-day
    start = event.get('start', {}).get('dateTime')
    if start:
      row = datetime.datetime.strptime(start, '%Y-%m-%dT%H:%M:%S%z').strftime('%-I:%M%p') + ' ' + row
    
    # add strikethough if end has passed
    end = event.get('end', {}).get('dateTime')
    if end:
      end = datetime.datetime.strptime(end, '%Y-%m-%dT%H:%M:%S%z')
      if end < now:
        striketext = ''
        for letter in row:
          striketext = striketext + letter + '\u0336'
        striketext = striketext.replace('&\u0336a\u0336m\u0336p\u0336;\u0336', '&amp;') # don't strikethrough &amp;
        row = striketext
    
    # find if there's a meeting url from attached conferenceData, or from searching location/description
    meetingUrl = None
    attachedMeetingUrl = event.get('conferenceData', {}).get('entryPoints')
    if attachedMeetingUrl:
      meetingUrl = next(x for x in attachedMeetingUrl if x['entryPointType'] == 'video').get('uri')
    elif findMeetingId(event.get('location', '')):
      meetingUrl = findMeetingId(event.get('location', ''))
    elif findMeetingId(event.get('description', '')):
      meetingUrl = findMeetingId(event.get('description', ''))
    # did we find one?
    if meetingUrl:
      row += ' ↗ | href=' + meetingUrl + ' '
    else:
      row += ' | '

    if useColors and event.get('color'):
      row += 'color=' + event.get('color') + ' '

    if event.get('icon'):
      row = event.get('icon') + ' ' + row

    print(row)
  
  print('---')
  print('↻ Refresh | refresh=true terminal=false')


def findMeetingId(text):
  # thanks to https://github.com/leits/MeetingBar/blob/master/MeetingBar/Constants.swift#L20
  meetingIdFormats = [
    "https?://meet.google.com/[a-z-]+",
    "https?://hangouts.google.com/[^\s]*",
    "https?://(?:[a-z0-9-.]+)?zoom.(?:us|com.cn)/(?:j|my)/[0-9a-zA-Z?=.]*",
    "zoommtg://([a-z0-9-.]+)?zoom.(us|com.cn)/join[^\s]*",
    "https?://teams.microsoft.com/l/meetup-join/[a-zA-Z0-9_%\/=\-\+\.?]+",
    "https?://([a-z0-9.-]+)?webex.com/[^\s]*",
    "https?://meet.jit.si/[^\s]*",
    "https?://([a-z0-9-.]+)?chime.aws/[^\s]*",
    "https?://meetings.ringcentral.com/[^\s]*",
    "https?://([a-z0-9.]+)?gotomeeting.com/[^\s]*",
    "https?://([a-z0-9.]+)?gotowebinar.com/[^\s]*",
    "https?://([a-z0-9.]+)?bluejeans.com/[^\s]*",
    "https?://8x8.vc/[^\s]*",
    "https?://event.demio.com/[^\s]*",
    "https?://join.me/[^\s]*",
    "https?://([a-z0-9.]+)?zoomgov.com/j/[a-zA-Z0-9?&=]+",
    "https?://whereby.com/[^\s]*",
    "https?://uberconference.com/[^\s]*",
    "https?://go.blizz.com/[^\s]*",
    "https?://go.teamviewer.com/[^\s]*",
    "https?://vsee.com/[^\s]*",
    "https?://meet.starleaf.com/[^\s]*",
    "https?://duo.app.goo.gl/[^\s]*",
    "https?://voovmeeting.com/[^\s]*",
    "https?://([a-z0-9-.]+)?workplace.com/[^\s]+",
    "https?://join.skype.com/[^\s]*",
    "https?://meet.lync.com/[^\s]*",
    "https?:\/\/(meet|join)\.[^\s]*\/[a-z0-9.]+/meet\/[A-Za-z0-9./]+",
    "https?://call.lifesizecloud.com/[^\s]*",
    "https?://((www|m)\.)?(youtube\.com|youtu\.be)/[^\s]*",
    "https?://meetings\.vonage\.com/[0-9]{9}",
    "https?://stream\.meet\.google\.com/stream/[a-z0-9-]+",
    "https?://meet\.around\.co/[^\s]*",
    "https://jam\.systems/[^\s]*",
    "(https|discord)://(www\.)?(canary\.)?discord(app)?\.([a-zA-Z]{2,})(.+)?"
  ]

  for urlFormat in meetingIdFormats:
    match = re.search(urlFormat, text, re.IGNORECASE)
    if match:
      return match.group(0)
  return None

if __name__ == '__main__':
  main()
