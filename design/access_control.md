# Access Control

## Terms

- `resource`: A resource is an object that is assigned to groups to determine the allowed access to the resource. FIX THIS!!!!

is one of a specified group or database objects that can be associated with a user. Permission for actions on a resource will
    be controlled through groups assigned by the owner. An example of a resources is an uploaded file. There is a database table representing
    the file and the user can assign groups to the file to control access. Note that groups are also used to assign permissions not related to resources,
    such as access to endpoints.

## Database Tables

Here are the main tables used in access control:

1. `Users` table: The users table represents the users of the system. A user can own resources, which can be created, modified and deleted.

2. `Groups` table: These are groups defined by a user to control access.
   - Important fields:
      - `owner`: The user Id for the owner of the group. This can be null, which can be thought of as system level groups.
      - `scope`: This is the scope for the group:
         - "resource" - Permissions for user in this group apply to actions on specific resources, according to a group list for that specific resource.
         - "user" - Permissions for users in this group apply to all resources or actions for a group owner.
         - "global" - Permissions for users in this group apply globally to resources or actions, independent of resource id or owner.
      - `type`: This is a label used to indicate a set of actions the users in this group can perform. The set of actions for the type are identified
        in the access control logic code in the initial implementation. (In future implementations, we may allow listing the actions allowed by a group
        to be stored in a database rather than from an enumerated from predefined types.)

3. `user_group` table: The table assigns a user to a group.
   - Important fields:
      - user: The user with whom the role is associated.
      - group: The group which the user is assigned.

4. `resource_group` table: This table associates groups with the resources, with only resource scoped groups being assigned here.
    Additionally, The group must have either the same owner id as the resource or have the owner by system level, (like public groups).
    The table will identify the resource by type and ID.

## Access Control Determination

There is an enumeration of permissions-requiring actions in the service, and associated targets for the given action. Some target types
are further specified by an ID (resources and users). In the case where the target is a resource, their is also a resource owner and
groups associated with these resources. Together these parameters determine permission for the action.

The Access determination parameters are listed below:

- user_id: The user doing the action.
- user_groups: The groups for this user.
- action: The action being done.
- target_type: The target for the action.
- target_id: (if applicable) An ID for the target. Applicable where the target is a resource or a user.
- target_owner: (if applicable) Only applicable to resources: the owner of the resource.
- target_groups: (if applicable) Only applicable to resources: the groups assigned to the resource.

### Examples Permission Lookup Scenarios

1. User creates a new project object.
    - user_id: user X
    - user_groups: (groups of user X)
    - action: "create"
    - target_type: "project"
    - target_owner: user X
    - target_groups: NA (no groups for created project)

2. User modifies a project object for which he is the owner.
    - user_id: user X
    - user_groups: (groups of user X)
    - action: "modify"
    - target_type: "project"
    - target_owner: user X
    - target_groups: (assigned groups of this specific project)

3. User creates a project that is to be owned by a different user.
    - user_id: user X
    - user_groups: (groups of user X)
    - action: "create"
    - target_type: "project"
    - target_owner: user Y (Here we are creating a project that will be owned by another user)
    - target_groups: NA (no groups for created project)

4. User accesses an endpoint.
    - user_id: user X
    - user_groups: (groups of user X)
    - action: "access_endpoint"
    - target_type: "protected_endpoint"
    - target_owner: NA
    - target_groups: NA

### Permission Lookup Function Signature

The following function is used to determine permission based on the passed in action and its associated parameters.

```python
def has_permission(
    user_id: int,
    user_groups: List[Group],
    action: str,
    target_type: str,
    target_id: Optional[int] = None,
    target_owner: Optional[int] = None,
    target_groups: Optional[List[Group]] = None
) -> bool:
    """
    Determine whether a given user is allowed to perform a given action on a target.

    Parameters:
      user_id: The ID of the user attempting the action.
      user_groups: Groups for the user.
      action: The named action (e.g., 'create', 'modify', 'access_endpoint').
      target_type: The type of target (e.g., 'project', 'document', 'protected_endpoint').
      target_id: (Optional) The ID of the target (if applicable).
      target_owner: (Optional) The owner ID, applicable for resource targets (if applicable).
      target_groups: (Optional) Groups associated with the target, for resource targets (if applicable).

    Returns:
      True if the action is allowed, False otherwise.
    """
```

## Actions and Group Types

### Actions

This is a list of actions requiring permission in the application.

1. Actions on Resources
    - Target: Table name used as target.
    - Actions:
        - view
        - modify
        - create
        - delete
        - assign_group_to_resource - Assign group to a resource. This is a special action in that it has two targets, the resource to which the group is assigned
            and the group that is being assigned to it. To accommodate this in the permission system, it is broken into two separate single-target actions:
            - assign_group_to_resources: This action requires a permission for the group: to assign it to some resource.
            - assign_groups_to_resource: This action requires a permission for the resource: to have some group assigned to it.
        - assign_group_to_user - Assign a group to a user.

2. Actions on Users
    - Target: "user"
    - Actions:
        - view: view the user details
            - not including password: no users can do this
            - not including name: this is granted to anyone who has access to a user resource
        - modify: only the user can modify the user object
        - create: only superusers can create a user
        - delete: only superuser and the user himself can delete a user
    - Notes:
        - The user is not considered a resource.

3. Actions on Endpoints
    - Targets:
        - "public_endpoint"
        - "protected_endpoint"
        - "private_endpoint"
    - Actions:
        - "access_endpoint"

### "Types"

Here is a list of types for groups given by the scope of the group. These are used to specify permissions granted by the groups.

- Types for groups of scope "resource"
    1. "view":
        - action "view" for any resource in this group.
    2. "update":
        - action "update" for any resource in this group.
    3. "full_edit":
        - actions  "create", "update", "delete" and "assign_groups_to_resource" for any resource in this group.
    4. "public_view":
        - Same as scope "resource" type "view" but system owned rather than user owned.
    5. "public_update":
        - Same as scope "resource" type "update" but system owned.
    6. "public_full_edit":
        - Same as scope "resource" type "full_edit" but system owned.
    7. "assign_group_to_resources":
        - action "assign_group_to_resources" for any group in this group.

- Types for groups of scope "user"
    1. "view":
        - action "view" for any resource owned by this user.
    2. "update":
        - action "update" for any resource owned by this user.
    3. "full_edit":
        - actions "create"/"update"/"delete" and "assign_resource_to_groups" for any resource owned by this user.
    4. "view_user":
        - action "view" for the user details
    5. "assign_group_to_resources":
        - action "assign_group_to_resources" for any group owned by this user.
    6. "assign_group_to_users":
        - action "assign_group_to_users" for any group owned by this user.
    7. "admin": Includes the following permissions:
        - includes permissions from scope "user" type "full_edit" (includes view and update permission)
        - includes permissions from scope "user" type "view_user"
        - includes permissions from scope "user" type "assign_group_to_resources"
        - includes permissions from scope "user" type "assign_group_to_users"

- Types for groups of scope "global"
    1. "protected_access":
        - action "access_endpoint" for "protected_endpoints"
    2. "private_access":
        - action "access_endpoint" for "private_endpoints"
    3. "admin": Includes the following permissions:
        - permissions from scope "user" type "admin", for all users
        - action "create" for target "user", for all users
        - action "view" for target "user", for all users
        - action "delete_user" for target "user", for all users
        - action "access_endpoint" for target "private_endpoint"

### Automatic Assignments

There will be some "automatic" group assignments. This is just for simplicity and to prevent users from losing access to public
resources or access to their own private resources:

- All users are given full control over resources they own, without need for any group assignment.
    - action "full_edit" for resources they own
    - action "assign_group" for groups they own
    - action "view" for their own user details
    - action "modify" for their own user details
    - action "delete" for their own user object
- All users are in the following groups implicitly, without the need to assign the group to the user.
    - group "public_view"
    - group "public_update"
    - group "public_full_edit"
    - group "protected_access"
- All users (logged in or not) are implicitly granted access to "public_access"

## Notes on Groups

### Assignment of Groups

One of the actions in the system is assigning resource to a group. As mentioned above, for the sake of the permission system this is
broken down into to separate actions, assigning the resource to _some unspecified group_, and assigning _some unspecified resource_ to the group. This accommodates
the two targets for the action be using into two actions with one target each.

An added confusion is that, to express the permission, one group is assigned to another group, so we must be careful about what each group means.

Let us examine the following scenario: User A wants to assign resource X to group Y, where resource X and group Y are owned by user B. User A must have the following permissions:

1. Permission to assign some resource to group Y

    - Option 0: User A is User B: A user can automatically assign groups he owns to resources he owns.

    - Option 1: Resource level permissions: Group Y is assigned to a group 1, where group 1:
        - Is owned by user B
        - Is of scope "resource"
        - The type includes the action "assign_resources_to_group"

        This lets user A assign resources to group Y.

    - Option 2: User level permissions: User A is assigned to a group 2, where group 2 is:
        - Is owned by user B
        - Is of scope "user"
        - The type includes the action "assign_resources_to_group".

        This lets user A assign resources to any group owned by user B.

    - Option 3: Global level permissions: User A is assigned to a group 3, where group 3 is:
        - Is of scope "global" (and hence has owner `null`)
        - The type includes the action "assign_resources_to_group" for all users.

2. Permission to assign resource X to some group

    - Option 0: User A is User B: A user can automatically assign groups he owns to resources he owns.

    - Option 1: Resource level permissions: Resource A is assigned to a group 4, where group 4:
        - Is owned by user B
        - Is of scope "resource"
        - The type includes the action "assign_resource_to_groups"

        This lets user A assign resources to group Y.

    - Option 2: User level permissions: User A is assigned to a group 5, where group 5 is:
        - Is owned by user B
        - Is of scope "user"
        - The type includes the action "assign_resource_to_groups".

        This lets user A assign resources to any group owned by user B.

    - Option 3: Global level permissions: User A is assigned to a group 6, where group 6 is:
        - Is of scope "global" (and hence has owner `null`)
        - The type includes the action "assign_resource_to_groups" for all users.

In this example above, we specified we were assigning resource X to group Y. The resource is a generic term tha represents a number
of possible objects. It could have been something like an project object, an uploaded file object or even a group object.
