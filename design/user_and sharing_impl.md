# User and Sharing Implementation 2/18/25

## Initial Implementation 2/17/25

The user and authorization system is designed to allow a user To grant the right for other uses to have different levels of access either to all the user content (organization level access) or to selected content (group level access). This includes some simplifying considerations to allow public access to users content. Additionally there is the capability for different system level roles to accommodate things such as super users or less powerful roles like moderators.

These capabilities are allowed by the users table, a user organization membership table and a number of tables related to groups and group memberships.

In the initial implementation we will only keep the users table. This means there is no organization or group level access granted to other users and that we have a single system superuser.

### User Management

Because this is a prototype service, we have a few user management peculiarities:

- Users are created by invitation only, by the system user. Therefore, there is no public sign up form for users.
- There is no safe email for the service, such as for resetting a password. Any such emails are sent **manually** by the system admin.

Actions:

1. Create User: (ADMIN ONLY) A form is filled out to create a new user. This action is done by an system admin only. The account is created with a dummy password
     and a "password reset" token is created for the user for the user to create a new password. (See "Initiate reset password")
2. Initiate Reset Password: (ADMIN ONLY) The admin does this on receiving a request to reset a password, through email. A rest password token is created and
    a reset password link in **MANUALLY** sent to the user by the system admin. The user will use this to set a new password.
3. Reset Password: (USER ONLY) This is the action by the user to reset the password. It requires a rest password token that must be send by the system admin.
4. Edit User: (USER ONLY) This allows the user to edit the user account, not including the password.
    - NOTE: The initial implementation does not allow the user to edit their username. There is no technical reason for this and this decision can be reviewed later. The username is currently set when the system admin creates the user.


