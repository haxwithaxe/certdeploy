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
- Fixed debug log call that should have been an info log call in the Docker update code
- Other documentation fixes

## Version 0.2.0 (alpha)
- Added the ability to retry pushing to clients
- As a side effect of the above, the server has a busier main loop so it may use more resources
- Added asynchronous pushing to clients (also a side effect of retying)
- Changed error output to be more uniform

## Version 0.2.1 (alpha)
- Removed a lot cruft from the docker images
- Removed a lot cruft from the sdist

## Version 0.2.2 (alpha)
- Bumped dependency versions
- Fixed missing f's on some f-strings
- Changed tests to match different performance
- Changed tests to match paramiko errors

## Version 0.3.0 (alpha)
Hopefully the last non-patch release alpha.

- Changed some environment variables to be explicitly for the server or client.
- Changed some config and environmental variable names ending in ``_file`` or ``_FILE`` to ``_filename`` (preserving case).
- Changed most config and environmental references to ``sftpd`` to ``sftp``. The `sftpd` client config is still the same.
- Added the ability to control the location of the log file of both the client and the server.
- Added the ability to control the log file location and log level of the SFTP component of both the client and server. The SFTP (paramiko) logs can just be noise sometimes so it's nice to be able to siphon them off and/or tune them down.
- Bumped dependency versions
- Removed bash based tests because of extreme fragility
- Removed all test and build requirements for docker-compose
- Added tons of tests to compensate for removing bash based tests
- Fixed a bunch of formatting
- Added tons of doc comments
- Added partial workarounds for https://github.com/moby/moby/issues/46341

### Logging changes
* In this release all logs go to `stdout` at ``ERROR`` log level by default.
* A log filename of ``/dev/null`` gets translated to a `logging.NullHandler`.

### Known bugs
See [this](https://github.com/moby/moby/issues/46341) upstream bug with docker. This means matching services by filters with any kind of explicit regex has been broken for a while. The docker service update code has been adjusted to directly get containers by name when the `name` option is given rather than using filters to get them. Filtering still works so long as it's used for substring matching and not regex (I know they're the same thing in this case but bugs will be bugs).

## Version 0.4.0 (alpha)
- Added the ability to load client connection configs from files in a directory. The purpose being to allow for more modular deployments.
- Added the ability to set the permissions on the lineage directories and certificates installed by the CertDeploy clients.

## Version 0.4.1 (alpha)
- Fixed error in Read the Docs config.

## Version 0.4.2 (alpha)
* Added more logging
* Adjusted server logging to use normal human friendly numbers

## Version 0.5.0 (alpha)
* Fixed default timeout passing bug
* Fixed SSH banner timeout by adding a config to adjust it
* Added traditional init system updaters (eg OpenRC or SysVInit)
* Bumped Docker module version
* Pushed versions up one in [ROADMAP.md](ROADMAP.md)
