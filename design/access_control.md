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
      - `permission_set`: This is a reference to an enumeration of lists of actions the users in this group can perform. (In future implementations,
        we may the fixed enumeration with a reference to a database list of actions, allowing more granular permission lists.)

3. `user_group` table: The table assigns a user to a group.
   - Important fields:
      - user: The user with whom the role is associated.
      - group: The group which the user is assigned.

4. `resource_group` table: This table associates groups with the resources, with only resource scoped groups being assigned here.
    Additionally, The group must have either the same owner id as the resource or have the owner by system level, (like public groups).
    The table will identify the resource by type and ID.

## Access Control Determination

There is an enumeration of actions in the service that require permission. Each action also has a target, which is what the action
is acting on. The target is specified by either a target type or a target type and a target id. Further, in the case where the target
type represents a "resource", as defined above, the permission determination depends on the owner of the resource and the groups assigned
to the resource. (A resource has an owner and a list of groups, with the owner possibly being null to represent the system being the owner.)

The Access determination parameters are listed below:

- user_id: The user doing the action.
- user_groups: The groups for this user.
- action: The action being done.
- target_type: The target for the action.
- target_id: (if applicable) An ID for the target. Examples are when the target is a resource or a user.
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
    - action: "update"
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
      action: The named action (e.g., 'create', 'update', 'access_endpoint').
      target_type: The type of target (e.g., 'project', 'document', 'protected_endpoint').
      target_id: (Optional) The ID of the target (if applicable).
      target_owner: (Optional) The owner ID, applicable for resource targets (if applicable).
      target_groups: (Optional) Groups associated with the target, for resource targets (if applicable).

    Returns:
      True if the action is allowed, False otherwise.
    """
```

## Actions

### Action Enumeration

This is a list of actions requiring permission in the application.

1. Actions on Resources
    - Target Type: Table name used as target type.
    - Actions:
        - view
        - update
        - create
        - delete
        - assign_group_to_resource - Assign group to a resource. This is a special action in that it has two targets, the resource to which the group is assigned
            and the group that is being assigned to it. To accommodate this in the permission system, it is broken into two separate single-target actions:
            - assign_group_to_resources: This action requires a permission for the group: to assign it to some resource. (Used only for groups, which are a resource)
            - assign_groups_to_resource: This action requires a permission for the resource: to have some group assigned to it. (Used for general resources)
        - assign_group_to_user - Assign a group to a user. (Used only for groups, which are a resource)

2. Actions on Users
    - Target Type: "user"
    - Actions:
        - view: view the user details
            - not including password: no users can view the password
            - not including name: this is granted to anyone who has access to a user resource
        - update: Modify fields for the user excluding password. (Typically only the user can update the user object)
        - update: Modify the users password. (Typically only the user can update the password)
        - create: Create a user
        - delete: Delete a use (Typically only superuser and the user himself can delete a user)
    - Notes:
        - The user is not considered a resource.

3. Actions on Endpoints: This is one implementation. Other permission types can be creates.
    - Target Types:
        - "public_endpoint": Accessible to all visitors, logged in or not.
        - "protected_endpoint": Accessible to all logged in users.
        - "private_endpoint": Accessible to superusers.
    - Actions:
        - "access_endpoint"

4. OTHER: There may be other actions that are implementation specific. An example could be "services" the user has access to based on subscriptions.

### Automatic Permission Assignments

There will be some "automatic" group assignments. This is just for simplicity and to prevent users from losing access to public
resources or access to their own private resources.

- All users are given full control over resources they own, without need for any group assignment.
    - action "full_edit" for resources they own
    - action "assign_groups_to_resource" for resources they own
    - action "assign_group_to_resources" for groups they own
    - action "assign_group_to_users" for groups they own
    - action "view" for their own user details
    - action "update" for their own user details
    - action "update_password" for their own user password
    - action "delete" for their own user object

The following automatic assignment makes an implicit group for public and protected access, so this does not have to be assigned for all users.

- All users are implicitly granted permission to "access_endpoint" for target type "protected_endpoint"
- All visitors (logged in or not) are implicitly granted permission to "access_endpoint" for target type "public_endpoint"

This is an implementation for public groups capabilities. This allows setting different levels of public capability for user resources. Note
that the name "public" can be construed as all visitors logged in or not, however there may be other endpoint restrictions limiting
who can actually view/edit these resources.

- All users are in the following groups implicitly, without the need to assign the group to the user.
    - group "public_view"
    - group "public_update"
    - group "public_full_edit"

## Permission Set Implementations

Here we give some more detailed implementations for permissions sets.

### Example

Here is a list of types for groups given by the scope of the group. These are used to specify permissions granted by the groups.

- Permission sets for groups of scope "resource"
    1. "resource:view":
        - action "view" for any resource in this group.
    2. "resource:update":
        - action "update" for any resource in this group.
    3. "resource:full_edit":
        - actions  "create", "update", "delete" and "assign_groups_to_resource" for any resource in this group.
    4. "resource:public_view":
        - Same as scope "resource" type "view" but system owned rather than user owned.
    5. "resource:public_update":
        - Same as scope "resource" type "update" but system owned.
    6. "resource:public_full_edit":
        - Same as scope "resource" type "full_edit" but system owned.
    7. "resource:assign_group_to_resources":
        - action "assign_group_to_resources" for any group in this group.

- Permission sets for groups of scope "user"
    1. "user:view":
        - action "view" for any resource owned by this user.
    2. "user:update":
        - action "update" and for any resource owned by this user.
    3. "user:full_edit":
        - actions "create"/"update"/"delete" and "assign_resource_to_groups" for any resource owned by this user.
    4. "user:view_user":
        - action "view" for the user details
    5. "user:assign_group_to_resources":
        - action "assign_group_to_resources" for any group owned by this user.
    6. "user:assign_group_to_users":
        - action "assign_group_to_users" for any group owned by this user.
    7. "user:admin": Includes the following permissions:
        - includes permissions from scope "user" type "full_edit" (includes view and update permission)
        - includes permissions from scope "user" type "view_user"
        - includes permissions from scope "user" type "assign_group_to_resources"
        - includes permissions from scope "user" type "assign_group_to_users"

- Types for groups of scope "global"
    1. "global:protected_access":
        - action "access_endpoint" for "protected_endpoint"
    2. "global:private_access":
        - action "access_endpoint" for "private_endpoints"
    3. "global:admin": Includes the following permissions:
        - permissions from scope "user" type "admin", for all users
        - action "create" for target "user", for all users
        - action "view" for target "user", for all users
        - action "delete_user" for target "user", for all users
        - action "access_endpoint" for target "private_endpoint"

## Notes on Assignment of Resources to Groups

One of the actions in the system is assigning a resource to a group. As mentioned above, for the sake of the permission system this is
broken down into to separate actions, assigning the resource to _some unspecified group_, and assigning _some unspecified resource_ to the group.
This accommodates the two targets for the action be using two actions with one target each.

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

============================
============================

## Chat Notes

### The Special Super User

We can update the groups so there is no "null" option for group ownership. Instead, we create a special superuser who will
own these special groups. The special user will be a formal user. In practice, we can create other superusers who can get
permissions for the same actions from the special super user.

Tradeoffs: Cleaner group dynamiscs for the super user? Do we compromise a conceptual difference by adding the special super user?

### Decoupling access permission from delegation permission

I use groups to control access to resources and to control assignment of groups to resources and users. With this I have one special
treatment of groups, since it has two actions that do not apply to other resources. The alternative is to have something like my groups
strictly control who can access resources (or other actions) and then a separate table that allows delegation of groups.

It seems like in bigger systems the second approach is more common. It is possibly better for security?

