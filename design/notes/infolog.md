# Infolog

## 2/18/25

progress:

- clean up design notes a little
- fixed a bug in initiate reset password (line had trailing slash that didn't work)
- adding logging initialization for app
- added some error checking and logging for user routes

## 2/17/25

progress:

- created the flask app
- added basic user management with a version of our user model.

next:

- fix up the user management
    - error checking
    - logging
    - generally, decide on coding standards and other service rules (and get text to communicate these rules)
- decide on web rules (and get some text to communicate these rules)
- more tables? (sharing tables? entity tables?): As soon as I add public sharing, I will add the public groups and then the ability to
    put an entity in a public group. It won't be a while until I use user org membership. MAYBE I LEAVE IT ALL OUT FOR NOW?
- add proper action authentication (using whatever is currnently implemented)
- start adding some of the application?
    - upload projects in API (support from web too, for later)
    - list projects on web
    - view projects on web
- add the API along with the API token access.

NOTES:

- currently do not let people edit their user name (no system requirement for this. Think if I want to add this later.)
- I think my user functions need better error handling (see chat notes on that)
- I need logging
- POSTGIS ISSUE WITH ALEMBIC: I had to add some code to get it to ignore the postgis tables. This means it will only autogen modifications
  tables in the metadata. If I delete a table, I think it might not get it. DOCUMENT THIS!

## 2/14/25

progress:

- more work on system desing

NOTES:

- ChatGPT said I could consider using a RBAC framework if the policy gets more complex or if I want more robustness. Since I don't know much about them, I'm not sure how much this is an enterprise level thing or something people often user.
    - "In summary, if your current system handles your needs well and you're not anticipating dramatic increases in complexity, rolling your own might suffice. But if you foresee rapid growth, dynamic policy needs, or integration complexities, transitioning to a dedicated framework can save time, reduce bugs, and enhance security in the long run."
- I might want to reconsider the complexity that I do have.


More chat on the RBAC Framework question:

================

How many people use a system like this versus their own simple role based system. Is this something big companies use or is it something people use on hobby projects or protoypes?

================

It's a mix. In the early stages or in hobby projects, many developers implement their own simple role-based systems because the requirements are limited and a custom solution is quicker to develop. However, as projects scale or require more granular control—especially in enterprise settings—many organizations either adopt robust frameworks (like Casbin, Oso, or OPA) or build in-depth custom solutions tailored to their unique needs.

**In Practice:**

- **Hobby/Prototype Projects:**  
  Developers often start with a simple, home-grown RBAC system, as it’s sufficient for small-scale apps and prototypes.

- **Large Companies & Complex Systems:**  
  Big companies tend to require more sophisticated, flexible, and maintainable access control solutions. Many of them either use well-established frameworks or develop custom systems with features akin to those frameworks to handle complex authorization logic, scalability challenges, and compliance requirements.

Ultimately, the decision depends on the complexity of your needs, your team's familiarity with the frameworks, and the long-term scalability goals of your application.

===========



## 2/7/25

notes:

- The scrap document today which includes lots of information about system design and I think part of that might be the access control system I want to use.
    I need to go through that and reiterate that and then review it to see if it actually makes sense. It's kind of a hodgepodge now.
    (Specifically I want the section actions and permission model number two along with the DB outline below it.)