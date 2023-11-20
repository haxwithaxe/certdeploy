# Plans are just informed wishful thinking.

## Version 0.5.0 (beta?)
- Notifications
   - Methods
      - Script
      - HTTP POST/GET
         - Or potentially the python library `notifiers` if they add ntfy support which is a hard requirement for haxwithaxe.
   - On adjustable severity levels
      - fatal - Only genuinely fatal errors if `fail_fast` is `True` this is equivalent to the `error` level.
      - error - Only on fatal errors and on errors that would be fatal if `fail_fast` were `True`.
      - status - Same as error but with messages on success events like successful push queue completion and sucessful completion of all updates.
      - log - Follow logging at the configured logging level or maybe at the log level appended to this option. We'll see how masochistic haxwithaxe is when he gets to this.

## Version 0.6.0 (beta)
- Ordered service updates
- Individually delayed service updates
   - Time delay after to allow for slow starting background tasks
   - Readiness based delay for docker containers and services
      - Healthcheck
      - ``running`` state
- Per service update on domain so that services that don't need to be updated for every lineage that gets pushed don't get disrupted.
