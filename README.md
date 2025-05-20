# BitBar/xBar/Argos Google Calendar Agenda

This is a Google Calendar Agenda script largely inspired by [MeetingBar](https://github.com/leits/MeetingBar) on macOS. I've personally only tested with Argos on Ubuntu, but it should work on any Linux distribution or macOS machine.

## Setup
0. Set up [xBar](https://xbarapp.com/) or [Argos](https://extensions.gnome.org/extension/1176/argos/) and Python with Pip on your Mac or Linux machine
1. Install [the Google Python Client Library](https://developers.google.com/calendar/quickstart/python) and [Humanize](https://pypi.org/project/humanize/) with  
`pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib humanize`
2. [Create a Google Workspace API Project](https://developers.google.com/workspace/guides/create-project), enable the Google Calendar API, create an oAuth client, and add yourself as a valid tester. Download the client credenetials file, rename to `credentials.json`, and move it to your xBar/Argos plugin directory.
3. Copy [`cal.5s.py`](https://github.com/leoherzog/bitbar-agenda/blob/main/cal.30s.py) from this repository to your xBar/Argos plugin directory
4. Edit the Calendar ID(s) that you'd like to check, as well as the (optional) Emoji icon, on line 22-31
5. If you'd like to colorize the events, set `useColors` to `true` on line 32
6. If you'd like to filter out events with certain names, add them to the `eventNamesToFilter` list on line 33
7. Mark the script as executible. It should pop open a web browser and ask for authentication, then begin listing events!

## License

The MIT License (MIT)

Copyright © 2021 Leo Herzog

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

## About Me

<a href="https://herzog.tech/" target="_blank">
  <img src="https://herzog.tech/signature/link.svg.png" width="32px" />
</a>
<a href="https://twitter.com/xd1936" target="_blank">
  <img src="https://herzog.tech/signature/twitter.svg.png" width="32px" />
</a>
<a href="https://facebook.com/xd1936" target="_blank">
  <img src="https://herzog.tech/signature/facebook.svg.png" width="32px" />
</a>
<a href="https://github.com/leoherzog" target="_blank">
  <img src="https://herzog.tech/signature/github.svg.png" width="32px" />
</a>
<a href="https://keybase.io/leoherzog" target="_blank">
  <img src="https://herzog.tech/signature/keybase.svg.png" width="32px" />
</a>
<a href="https://www.linkedin.com/in/leoherzog" target="_blank">
  <img src="https://herzog.tech/signature/linkedin.svg.png" width="32px" />
</a>
<a href="https://hope.edu/directory/people/herzog-leo/" target="_blank">
  <img src="https://herzog.tech/signature/anchor.svg.png" width="32px" />
</a>
<br />
<a href="https://www.buymeacoffee.com/leoherzog" target="_blank">
  <img src="https://cdn.buymeacoffee.com/buttons/lato-black.png" alt="Buy Me A Coffee" width="217px" />
</a>