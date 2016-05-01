# Changelog


## 0.3.0


### Features

 * Added new buffer which displays detailed info about container:
  * Process tree inside container, brief logs, labels, realtime resource usage, networking...
  * Can be activated by hitting `<enter>` on a container in main listing.
 * Pressing `!` while in main listing disables live updates: you don't need to worry about accidentally removing a container when interface updates.
 * Main listing table displays responsively now.
 * `sen` is now able to survive a docker daemon restart.
 * When removing buffers, last accessed buffer will be displayed instead of main listing.


### Bug fixes

 * Make `sen` work with docker `1.10` and `1.11`.
 * Fix race condition which happened quite often and resulted in traceback with message
   ```
   AssertionError: rows, render mismatch
   ```
 * When listing containers or images via docker engine API, it's possible to get 500; `sen` retries the call several times now.
 * `sen` won't freeze when opening a new buffer while there are multiple calls against docker engine pending.

There are also other small fixes and improvements. `sen` contains more tests so it should be more stable in future.

