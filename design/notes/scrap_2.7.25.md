# 2/7/25

## Basic Site

### Website Pages

Authentication:

- Login/Logout (cookie)

User:

- Edit account
- Create account
- Delete account

Projects:

- View Project list, including filters and ordering
- Open Project: Display a map for the project
- (Edit project???)

### API

Authentication:

- Login (token)
- Logout (token)

Project:

- Create Project: Create a new project
- Update Project: Edit sources and layers for a project
- Delete Project: Delete a project

File: (TBD if this is included with project.)

- Upload File: Upload a file, tied to this project
- Delete File: delete a file
- Update File: Create a new version of a file

=============================

## Actions

Authentication:

- Login (cookie)
- Login (token)
- Logout (cookie)
- Logout (token)
- Refresh Cookie?
- Refresh Token?

Access:

- Access endpoint (TBD if by endpoint or endpoint type)
- Access service (This might be some resource you have to pay for)

User/Account:

- Create account
- Update account
- Update Account Credentials, password (and email/phone?)
- Delete account
- View Account Info (profile)

Projects:

- Create Project: Create a new project
- Update Project: Edit sources and layers for a project
- Delete Project: Delete a project
- View Project: View a project

File: (TBD if this is included with project.)

- Upload File: Upload a file, tied to this project (This is also used for update, which is to replace an existing file)
- Delete File: Delete a file
- View File: Download a file

==========================

### Sharing

Sharing Actions:

- View access for a user/entity pair
- Create access for a user/entity pair
- Update access for a user/entity pair
- Delete access for a user/entity pair

- Assign view access for a user/entity pair
- Assign create access for a user/entity pair
- Assign update access for a user/entity pair
- Assign delete access for a user/entity pair



Permission Models:

1. Group holds permissions; Unified groups
    - There are three scopes of group. This specifies what the permissions cover
        - entity: permissions apply only to entities associated with the group
        - user: Permissions apply to the user who owns the group
        - general: Permissions apply independent of entity or user.
    - Groups have an owner, which may be null. Null indicates a system-wide group
    - Groups can only be assigned to an entity if it is owned by the same user as the entity or if the user is null.
    - Groups carry access, as specified by:
        - actor: The user who is doing the action (subject)
        - action: The action being done (verb)
        - target: What the action is acting on (direct object)
    - Target specification:
        - simple target: no ID
            - access endpoint
            - access service (?)
        - user: requires an ID
            - update user
            - update uer credentials?
            - create user (? - no id here, I think)
            - delete use
        - "entity": requires an Id and the target has associated groups.
            - view project
            - update project
            - create project
            - delete project
    - Special Case: Multi-target actions: If an action has multiple targets, it should be decomposed into single target actions:
        - Associate a group with an entity: MULTI TARGET: (group, entity)
            - Associate a group (with some entity)
            - Associate an entity (with some group)
        - Associate a group with a user: NOT MULTI TARGET: (group) There is no differentiation based on user.

    Actions: (Related to groups)

    - Create/Update/Delete a group owned by a given user and a given permission level (Updating permissions might be dangerous)
    - Associate/Remove a group (with some entity)
    - Associate/Remove an entity (with some group)
    - Assign/Remove a user to a group
    - Assign/Remove delegation authority for a given user

    I THINK THIS IS TOO PERMISSIVE. MAYBE #2 IS SAFER!

2. Entity groups separated from "delegation" permission (for a meaning of delegation)

    NOTE: THIS NEEDS REVIEW FOR CONSISTENCY

    - Entity access is controlled with groups.
        - TBD: group membership has a role that dictates permission or group itself dictates permission. Lean towards roles have permission, to match org membership.
    - Group management is controlled by permission levels of the organization member (only certain are granted group management permission)
        - I might want a simplification: groups can be member (maybe different access types) and admin. Admin can do all delegating and oly admin can delegate.

    - There are two scopes of group. This specifies what the permissions cover
        - entity: permissions apply only to entities associated with the group
        - general: Permissions apply independent of entity or user. ???
    - Groups have an owner, which may be null. Null indicates a system level 
    - Groups can only be assigned to an entity if it is owned by the same user as the entity or if the user is null.
    - Groups carry access, as specified by:
        - actor: The user who is doing the action (subject)
        - action: The action being done (verb)
        - target: What the action is acting on (direct object)
            - entity type
            - id
            - associated groups of the given entity (pass this in probably)
    - Special Case: Multi-target actions: If an action has multiple targets, it should be decomposed into single target actions:
        - Associate a group with an entity: MULTI TARGET: (group, entity)
            - Associate a group (with some entity)
            - Associate an entity (with some group)
    - The UserOrgMember table has a role indicating the users level orf authority for the user/org.
        - manage groups
        - manage users (users membership in groups)

    - Other authorization:
        - Endpoint: controlled by membership in system org
            - access endpoint
            - access service (?)
        - user: controlled by membership in user org (or system org)
            - update user
            - update uer credentials?
            - create user (? - no id here, I think)
            - delete use
        - "entity": controlled by groups or membership in user org or system org
            - view project
            - update project
            - create project
            - delete project

    - System User/Org: We do have a system user/org. 
        - membership in the system org determines access for things like access points or other system level objects
        - WE STILL HAVE NULL GROUPS: this is for "public", as distinct from groups the system uses (like maybe moderators and sysadmins)
            - We probably have no create for entity, since you can't create something that already exists. TBD on delete.

    Actions:

    - Entity Management:
        - Associate/Remove a group (with some entity)
        - Associate/Remove an entity (with some group)
    - Group Management:
        - Create/Update/Delete a group owned by a given user and a given permission level (Updating permissions might be dangerous)
        - Assign/Remove a user to a group

    Permission Levels:

    - entity group membership:
        - view
        - update (and view)
        - create/update/delete (full_edit) (and view)
    - organization membership:
        - view
        - update (and view)
        - create/update/delete (and view)
        - admin (and create, update, delete) Allows group management, omits editing the user/org.
        - superuser (and admin) (includes all user permissions)
    - TBD: user profile permissions.
        - Option 1: Make use an entity with groups specifying profile view capability (not create/update/delete).
        - OPtion 2: The same access for everyone (TBD if it should be private or public. Specify parts for public.)

        I lean towards #2, with all profiles being accessible, excluding email/phone/password (TBD if there are others: memberships?) 


===============================
===============================

I have an DB outline for the system, emphasizing the access control for now.

**Users**

The system will have individual users and organizations who can own the content. We have chosen to make both of these "user" objects,
so that a user may represent "Dean Wormer" or "Faber College". We also have a membership mechanism so "Dean Wormer" can be a member or
the "Faber College" organization.

1. User Object:
   - id (primary key)
   - username (unique)
   - email (unique)
   - password_hash
   - status (e.g. active/suspended/deleted)
   - is_system_org (boolean, default false - true intended for single main system user)
   - created_at
   - updated_at

   Users of the system. These can represent individuals or organizations. A user 

2. UserAsOrgMembership Object:
   - id (primary key)
   - org_id (foreign key to User representing the org)
   - member_id (foreign key to User)
   - role (e.g. member/admin/superuser)
   - status (e.g. active/invited/suspended)
   - created_at
   - updated_at
   - invited_by (foreign key to User)

**Access**

Access is controlled with access groups and memberships.

1. AccessGroup Object:
   - id (primary key)
   - name
   - description
   - created_at
   - updated_at
   - created_by (foreign key to User)

2. AccessMembership Object:
   - id (primary key)
   - group_id (foreign key to EntityAccessGroup)
   - user_id (foreign key to User)
   - permission_level (e.g. view/edit/manage)
   - created_at
   - updated_at
   - added_by (foreign key to User)


**Entity and "Traits"**

We have created "traits" which we can let database objects inherit from. We have three traits: 

- access control - groups
- properties (key-value pair)
- comments

TBD how we control which traits are allowed for a given entity type. Maybe just by implementation?

1. EntityContext Object (associates access object with access groups):
   - id (primary key)
   - created_at
   - updated_at
   - created_by (foreign key to User)
   - status (e.g. active/deleted)
   - ???: add an entity type?

   TBD if we want to allow multiple permission levels for a user or if we restrict it to a unique permission level.

   At the system level, we will not constrain the permission levels allowed based on the type of entity referenced. Non-applicable levels will be ignored.

2. EntityGroups Object: (Holds groups for the given entity)
    - id (primary key)
    - entity_context_id
    - group_id

3. EntityProperties Object:
   - id (primary key)
   - entity_context_id (foreign key)
   - property_key (e.g., "avatar_url", "bio", "location", "org_description")
   - property_value
   - created_at
   - updated_at

   At the system level we will not constrain allowed property keys or values. Client applications may constrain that.

4. EntityComments Object:
    - ...

    Comments are intended as discussion related to a corresponding entity rather than quick comments like "Nice!". 

    No hierarchical comments.


**Application Content**

This is the actual shared map data. It consists of a map project which will probably include map sources and map layers similar to the map Libre SDK model. We will also allow file uploads for users but every file upload must be tied to a project just to make sure we don't have orphans. Projects may reference uploaded files that are referenced to to other projects.)

The data sources for project can reference uploaded files from the current project or a different project or they may reference external files.

I've included this for context only. We don't really be emphasizing this part of the application right now.

1. Project Object:
   - id (primary key)
   - name
   - owner_id (foreign key to User)
   - entity_context_id (foreign key to AccessContext. Probably 1:1)
   - status (e.g. active/archived/deleted)
   - created_at
   - updated_at
   - last_modified_by (foreign key to User)

2. ProjectSource Object:
    - id (primary key)
    - project_id (foreign key to Project)
    - ... (data for the data source, as uploaded file or external link)

3. ProjectLayer Object:
    - id (primary key)
    - project_id (foreign key to Project)
    - ... (data for the map layer)

4. ProjectFileUploads:
   - id (primary key)
   - owner_id
   - project_id (foreign key to Project)
   - entity_context_id (foreign key to AccessContext. Probably 1:1)
   - status (e.g. active/archived/deleted)
   - ... (data for stored file content)

   Project and ProjectFile permissions can be different. One specific use of this is so that a public project can hold some protected project data as well as public data. On the other hand, the project may have a file with less restrictive access, if the file is something you want to share with other uesrs but the parent project is a private project used for building/managing the file.

===============================
===============================

## Entity Notes

- The entity idea is that entities could have: group access controls, properties, comments.
- We don't need all entities to have all these features. We could restrict or choose to only implement some of the features to a given entity type.
    This way each of these features could be a trait for any entity. We might just want to add an entity type field.
- I wonder if my model is too permissive. I should figure out what exactly I want to allow.
    - It is almost like all group actions should go under one category, delegation, with a level that indicates what actions you are allowed to delegate.
        - creating a group or editting group permissions or assigning a group to a user all grant user permissions
    - editing group permissions is very dangerous, because you might grant someone permission that they shouldn't get. 

ASIDE: GAAA! This gets complicated when you trace history, which would be worthwhile. Maybe that is just done as a history rather than in the database tables.