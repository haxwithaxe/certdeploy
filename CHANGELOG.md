# Changelog

## Version 0.1.0 (alpha)

- Initial alpha release. Still some things left to do but it should work as expected in most cases especially those close to default.

## Version 0.1.1 (alpha)

- Fixed some logging
- Filled out the CONTRIBUTING.md
- Cleaned up testing some

## Version 0.1.2 (alpha)
- Added/removed some files included/excluded by mistake
- Added server install docs
- Added systemd unit examples
- Fixed debug log call that should have been an info log call in the Docker update code.
- Other documentation fixes

## Version 0.2.0 (alpha)
- Added the ability to retry pushing to clients
- As a side effect of the above, the server has a busier main loop so it may use more resources
- Added asynchronous pushing to clients (also a side effect of retying)
- Changed error output to be more uniform
