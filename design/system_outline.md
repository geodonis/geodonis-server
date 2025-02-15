# Application Outline 2/14/25

Here is the data model and access control outline for an application.

## Data Model

I have an DB outline for the system, emphasizing the access control for now.

### Users

The system will have individuals and organizations who can own the content. In the case of an organization, any content owned by the organization is labeled as organization content and not as content from a member who created it. An example might be a county nature preserve. Any content from the nature preserve such as trail maps would be owned by the nature preserve and not by individuals who work on the nature preserves behalf.

To implement this system we will have the single concept of a user to represent either an individual or a user content.

In the case of an organization, the organization's user account should be viewed as a _root_ account for that organization. Work done by individual users on behalf of the organization should be done from their user account rather than the root account. The root account should be reserved for a small number of actions that can be done only by that account.

1. User

    Users of the system. These can represent individuals or organizations.

    **Users Table**:

    - id (primary key)
    - username (unique)
    - email (unique)
    - password_hash
    - status (options: [active, suspended, deleted])
    - is_super_user (boolean, default false - true intended for single main system user)
    - created_at
    - updated_at

### Content

Content owned by users has a number of possible generic traits. This includes shared access, properties and comments. To implement these different standard traits for system content, we introduce an "entity" object, which can be seen as a base class for any content object. Each content object can be associated with an "entity context" object if it chooses to inherit one or more of the allowed traits. Traits can then be associated with the entity context object with a formal database association rather than having to associate these traits with the different individual content objects.

We do not enforce which individual traits a given content type may have at the database level. It's thus up to the application to choose to use the traits it desires for a given content type. Implementation wise, this looks more like a base class with all functionality. Philosophically wise, we choose to interpret this as being able to select different traits for a given content type.

1. Entity "Base Class"

    The content traits in the system are all associated with a single database type, the entity context object. The content objects of different types are associated with an entity context object in a one to one mapping to obtain the associated traits.

    Note that groups can only be assigned to content where the group is owned by the same user as the content or the group has the NULL owner.

    **EntityContexts Table**:

    - id (primary key)
    - entity_type: the type of entity

2. Group Assignment Trait

    Entities can be assigned to a group where user membership in this group is used to control access to those entities.

    **EntityGroups Table**:

    - id (primary key)
    - entity_context_id
    - group_id

3. Properties Trait

    Entities can be assigned to properties using the entity properties trait.

    NOTE: At the system level we will not constrain allowed property keys or values. Client applications may constrain that.

    **EntityProperties Table**:

   - id (primary key)
   - entity_context_id (foreign key)
   - property_key (e.g., "avatar_url", "bio", "location", "org_description")
   - property_value

4. Comments Trait

    **TO BE IMPLEMENTED LATER**

    Entities can be assigned comments using the entity comments trait.

    Here comments are meant as a discussion associated with the entity. The comments are not hierarchical.

    **EntityComments Table**:
    - ...

### Access

Authority to content for a given user (user A) is granted through memberships of two kinds (1) user (use B) level access, which grants access at a
specified level to all content owned by the user B and (2) content level access, which grants access to specific content owned by user B.

1. User Level Access

    A user can give authority to other users by granting them membership. The associated role determines their level of access.

    **UserMemberships Table**:

   - id (primary key)
   - owner_id (foreign key to User representing the content owner)
   - member_id (foreign key to User representing the member)
   - role (options: [view, update, full_edit, admin])
   - status (options: [active, invited, suspended])
   - created_at
   - updated_at
   - invited_by (foreign key to User)

2. Content level Access

    A user can create "groups" to which content (entities) can be assigned. Membership in the group grants access to any entities associated with this group, with the level of access determined by a "permission level" associated with the membership.

    There can also be groups assigned a NULL user. This means it is a public group.

    Notes:

    - Groups can only be assigned to content where the group is owned by the same user as the content or the group has the NULL owner.
    - Authority to grant membership for a specific user can be done by the user or by those granted permission by the user. No users have authority to grant users membership to the public groups.
    - Membership in the public group is implicit for all users. See the implementation of public groups and the associated permission levels.

    **Groups Table**:

    - id (primary key)
    - user_id (foreign key to the user)
    - name
    - description
    - created_at
    - updated_at
    - created_by (foreign key to User)

    **GroupMemberships Table**:

    - id (primary key)
    - group_id (foreign key to EntityAccessGroup)
    - user_id (foreign key to User; NULL OK)
    - permission_level (options: [view, update])
    - created_at
    - updated_at
    - added_by (foreign key to User)

### Application Content

At the application level, content types are defined and, if needed, linked to an entity context object in a one to one mapping to use the different entity traits.

I've included this for context only. We don't really be emphasizing this part of the application right now.

In Geodonis, the application content is map data.

1. Map Project

    A map project includes map sources and map layers, similar to the map Libre SDK model. The project also has associated uploaded files, though they are controlled as a separate entity, for example with separate permissions.

    A project object is associated with an entity to use the traits: group access, properties, comments.

    **Projects Table**:

    - id (primary key)
    - name
    - owner_id (foreign key to User)
    - entity_context_id (foreign key to EntityContext. 1:1)
    - version
    - created_at
    - updated_at

    **ProjectSources Table**:

    - id (primary key)
    - project_id (foreign key to Project)
    - ... (data for the data source, as uploaded file or external link)

    **ProjectLayers Table**:

    - id (primary key)
    - project_id (foreign key to Project)
    - ... (data for the map layer)

2. File Uploads

    The uploaded files. They are associated with a project to enforce that there are not orphans. However, an uploaded file may be referenced from 
    projects other projects and the permission settings for the upload may differ from the project that owns it.

    A project object is associated with an entity to use the traits: group access, properties, comments.

    File uploads are immutable. A specific version of file can only be created or deleted but not updated. Adding a new version does not delete the old version.

    **ProjectFileUploads Table**:

    - id (primary key)
    - owner_id
    - project_id (foreign key to Project)
    - entity_context_id (foreign key to EntityContext. 1:1)
    - version (primary key)
    - ... (data for stored file content)

## Access Implementation

Below are the groups and roles assigned for the implementation of the access control:

1. The super user: There is one user created that is the super user for the system. This will control groups that have system level access. This is the only user that has the "is_super_user"  flag set to true.
2. User Member Roles: These are the allowed roles for user level membership
    - view: view
    - update: view, update
    - full_edit: view, create, update, delete
    - admin: most permissions given to the "owner" user (some exceptions)
3. Entity Group Permission Levels:
    - view: view
    - update: view, update
4. Superuser Membership Roles: TO BE ADDED LATER. Only assignable by the super user or someone granted this superuser privilege.
5. Public groups: These are the public groups and the role in which all users are implicitly assigned.
    - "public_view": "view" role
    - "public_update": "update" role

## Service Components

### Authorization

The web service will include both web pages and an API, which will be accessed both from the web pages and from mobile devices.

- Web pages: HTTP-only cookies
- API: Tokens or HTTP-only cookies.

The HTTP-only cookie authorization should include csrf protection.

The actions that will be authorized and the information used to authorize the action:

**Endpoint Access**

Cases:

- Accessing an endpoint requiring login
- Accessing an endpoint requiring system admin

FUTURE: We may wont to combine this with the function below, if particular when we add special membership groups for the super user.

**Internal Action Access**

Authorization Function Arguments:

- acting_user: user object, including user and group memberships
- action: string action name identify the action with the type of object acted on.
- target_owner_id - user ID of target owner, if applicable (user management, sharing, entities)
- target groups - groups for a target entity, if applicable (entities only)
- additional_parameters: map {string: any}. Additional parameters not needed for authorization but for logging

Cases:

- User Management
    - Create, Update, Delete a user
        - Validation parameters
            - acting_user: acting user
            - action: "create_user", "update_user", "delete_user"
            - target_owner_id: user (if not create)
            - target_groups: NULL
            - additional_parameters: NULL
        - Authorized users:
            - system super user
            - target owner
    - Create password reset token
        - Validation parameters
            - acting_user: acting user
            - action: "create_password_reset_token"
            - target_owner_id: user (if not create)
            - target_groups: NULL
            - additional_parameters: NULL
        - Authorized users:
            - system super user
- User Sharing:
    - Create, Update, Delete a user level membership for user R with a user O.
        - Validation parameters
            - acting_user: acting user
            - action: "create_user_membership", "update_user_membership", "delete_user_membership"
            - target_owner_id: user O
            - target_groups: NULL
            - additional_parameters:
                - user_membership_id: (if not create)
                - member_id: user R ID
                - role: role
        - Authorized users: (same for all sharing actions)
            - system super user
            - target owner
            - a user who is a member of the target owner with role "admin"
    - Create, Update, Delete a group level membership for user R in a group owned by a user O.
        - Validation parameters
            - acting_user: acting user
            - action: "create_group_membership", "update_group_membership", "delete_group_membership"
            - target_owner_id: user O
            - target_groups: NULL
            - additional_parameters:
                - group_id
                - group_membership_id (if not create)
                - member_id: user R ID
                - permission_level: permission_level
        - Authorized users: (same for all sharing actions)
    - Create, Update, Delete a group for a user O
        - Validation parameters
            - acting_user: acting user
            - action: "create_group", "update_group", "delete_group
            - target_owner_id: user O
            - target_groups: NULL
            - additional_parameters:
                - group_id (if not create)
        - Authorized users: (same for all sharing actions)
- Entity Access:
    - View, Update, Create, Delete an entity owned by user O
        - Validation parameters
            - acting_user: acting user
            - action: "view_entity", "update_entity", "create_entity", "delete_entity"
            - target_owner_id: user O
            - target_groups: list of groups associated with the entity
            - additional_parameters:
                - entity_id: if not create
                - entity_type: entity type
                - X_id: id of the object pointing to the entity (where X is the table name)
        - Authorized users:
            - system super user,
            - target owner
            - a user who is a member of the target owner with appropriate role
            - a user who is a member of a group associated with the target entity with appropriate permissions

### User

These are the user management actions.

Because this is a prototype service, we have a few user management peculiarities:

- There is no public sign form for users. Users must be invited by the system admin.
- There is no safe email for the service, such as for resetting a password. Any such emails are done **manually** by the system admin.

Actions:

1. Create User: (ADMIN ONLY) A form is filled out to create a new user. This action is done by an system admin only. The account is created with a dummy password
     and a "password reset" token is created for the user for the user to create a new password. (See "Initiate reset password")
2. Initiate Reset Password: (ADMIN ONLY) The admin does this on receiving a request to reset a password, through email. A rest password token is created and
    a reset password link in **MANUALLY** sent to the user by the system admin. The user will use this to set a new password.
3. Reset_Password: (USER ONLY) This is the action by the user to reset the password. It requires a rest password token that must be send by the system admin.
4. Edit_User: (USER ONLY) This allows the user to edit the user account, not including the password.

### Sharing

TO BE FILLED IN

## Application Level 

TO BE FILLED IN