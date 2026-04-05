Store private material for the workspace CLI here.

Expected private key path:
- `.secrets/id_workspace`

Notes:
- Do not commit real secrets.
- The CLI never prints the private key contents.
- SSH clones use the key path only through `GIT_SSH_COMMAND`.
