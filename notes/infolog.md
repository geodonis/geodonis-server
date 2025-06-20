# Infolog

## 6/20/25

progress:

- update the code for protected submit:
    - always include the handler on the body listening for a submit from a form with tag 'data-protected-submit'
    - developer labels protected forms with the tag 'data-protected-submit' to attach the csrf.
    - handle different responses properly, updating the web page.


notes:

- I think I want a "working" animation while we wait for the submit to be processed. And maybe disable the submit button.

## 6/19/25

progress:

- worked on jwt for the web site

notes:

- the email is case sensitive for login (probably we have other similar errors) Or is this good/ok?
- I need to test/debug thoroughly
- I think the code is really ugly because the assistant followed different conventions and wrote code lacking some knwoledge. Review and clean it up.
- I still have the session table. I might want to make a manual migration to remove it.
    - It doesn't look like it is  in the existing migrations. Investigate and fix (actual db, migrations, etc) if anything is wrong.
- I should uninstall some modules from the venv. (flask session, flask login)
    - update others?
- I can use the external project for the app, with jwt login where needed (I can use static pages - no template needed)
- I have a problem where I get a json error rathe than an HTML error. I think it is when I have a token loaded that is invalid, or something like that. I am not sure if that is it but the logic that decides if an error is from a browser or api is not good.
- Because I use "url_prefix" for the routes, I think the api endpoints are not correct.

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