# Changelog


## 0.5.1


### Features

 * Support both `docker-py` `1.x` and `2.x`.

### Bug Fixes

 * Don't strip leading whitespace when displaying logs, or when inspecting.



## 0.5.0


### Features

 * Realtime events from docker daemon refresh container info and image info buffers.
 * Layer size is now displayed in layer tree view. [#115](https://github.com/TomasTomecek/sen/issues/115)
 * ANSI escape sequences are now stripped from container logs. [#67](https://github.com/TomasTomecek/sen/issues/67)


### Bug fixes

 * Viewing container logs should no longer break sen's interface. [#112](https://github.com/TomasTomecek/sen/issues/112)
 * Various issues, race conditions, code quality and performance was either fixed or improved.


## 0.4.0


### Changes

 * `q` keybind was altered slightly: it removes current buffer; if there's no buffer to remove, it closes the application
  * This change was requested over here: [#21](https://github.com/TomasTomecek/sen/issues/21)
 * Main listing is now sorted by date when the object was changed [#89](https://github.com/TomasTomecek/sen/pulls/89) (thanks to [@**f-cap**](https://github.com/f-cap))
  * This should move e.g. running containers to the top of the list


### Features

 * There's a new command system being introduced
  * Can be activated with `:`
  * You can use `help` command for getting more info about commands
   * calling `help` shows help buffer for current buffer
   * calling `help command` displays help for the selected command
  * Using keybind `?` now displays name of commands sen actually uses
  * The command system is **experimental** and subject to change (some commands will be changed or removed in future)
 * New listing command: open in browser [#94](https://github.com/TomasTomecek/sen/pulls/94) (thanks to [@**f-cap**](https://github.com/f-cap))
  * You no longer need to copy-paste IP address of a container to browser, just hit `b` in main listing buffer and sen will open the `http://{ip_address}:{port}` of the particular container in your browser
 * Understand new image format introduced in 1.10
  * Layers are displayed in image info buffer

### Bug fixes

 * sen is able to start even when there are no images nor containers [#86](https://github.com/TomasTomecek/sen/pulls/86) (thanks to [@**f-cap**](https://github.com/f-cap))
 * Persist filters and searching when changing buffers [#85](https://github.com/TomasTomecek/sen/issues/85)

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

