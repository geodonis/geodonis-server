# Infolog

## 6/18/25

Repurpose of this project from a geodata sharing project to the map application.

progress:

- added a file upload endpoint
- added a reference to pull in static code from an external location (the pacman project)

notes:

- If I want to uploads from the map I will need the csrf token in the web page. I wanted to keep the map app in a separate repository, but I think it'd be easiest just to put it in here.
- Questions:
    - If I'm allowing people to have external development on modules, I want to make sure they can't do file uploads. I only want to file uploads and potentially other functionality to be available from my own modules. I will work this problem out later when I actually have other users developing modules.
        - One thing I thought about was having a special version of the app it would allow loading scripts from other servers. I could disable any access, such as by not including csrf from this version possibly.
    - I will have to make sure the user doesn't get logged out if they are doing uploads. And probably do this by letting them stay logged in for a long time, like weeks rather than two hours or whatever I currently haven't set at.

Next?:

- Put the app in this server!
- Deploy the server! (no uploads yet, just get it working)
- Start the gps point collection module!