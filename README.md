[![Project generated with PyScaffold](https://img.shields.io/badge/-PyScaffold-005CA0?logo=pyscaffold)](https://pyscaffold.org/)

# certdeploy

    A tool to automatically sync certificates and update services.

This tool has two parts:
1. The "server". Which is implemented as a deploy hook for certbot and a docker container that bundles the deploy hook with certbot.
1. The "client". Which when run as a script moves certs from a staging directory to another directory, updates services after it moves the certs and can be run via cron or systemd timer and the "client" daemon which also runs an SFTP server that the CertDepoly server can connect to directly.

This tool can be used in a few different ways:
* As a set of docker containers automatically renewing and distributing certs then updating docker services and restarting docker containers via the Docker API.
* As scripts embeded in regular linux systems.
* As a mix of both.


## The Server
There are three parts to the server.
1. The certbot hook, which is run by Certbot as a deploy hook. This queues updates to be pushed to clients.
1. The command, which can be used to push certs to clients directly or try to renew certs immediately. This is useful for testing setups.
1. The daemon, which runs ``certbot renew`` on an interval (and indirectly ``certdeploy-server`` as a hook when certs are renewed). It also processes the push queue. This is optional, but is the default in the server docker container.

### Commandline Options for the command/daemon
* `--lineage` - The path of a lineage (eg `/etc/letsencrypt/live/example.com`). This is mutually exclusive with `--daemon`.
* `--domains` - A space separated list of domains as a single string (eg `"www.example.com example.com"`). This is mutually exclusive with `--daemon`.
* `--push` - Run the daemon only until the queue is empty and all pushes have been processed. When used with `--lineage` and `--domains` it populates the queue and then runs the daemon until the push is complete.
* `--config` - The path to the config file.
* `--daemon` - Run the daemon. Without this option the server command will run once and exit.
* `--renew` - Run the cert renewal part of the daemon once and exit.
* `--log-level` - Set the log level to `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL`.

#### Examples
To run these in the running docker container prefix the commands with `docker container exec <container name>`.
* Run the daemon with a custom config file location and log level.
    ```
    certdeploy-server --daemon --config /path/to/server.yml --log-level INFO
    ```
* Run the command to force deploying certs. Where `/etc/letsencrypt/live/` is the path to the lineages. Certbot puts it there by default. The server script can only handle one lineage at a time.
    ```
    certdeploy-server --push --lineage /etc/letsencrypt/live/example.com --domains "www.example.com example.com"
    ```
* Run the command to try to renew certs. This will not cause the certs to be pushed to clients unless the daemon is running or is run after the CertDeploy deploy hook is run.
    ```
    certdeploy-server --renew
    ```
* Run the command to push an existing push queue, but without adding to the queue.
    ```
    certdeploy-server --push
    ```

### Enviroment Variables
Commandline options override environment variables.
* ``CERTDEPLOY_RENEW_ONLY`` - If set to `true` it is the equivalent of ``--renew``.
* ``CERTDEPLOY_SERVER_DAEMON`` - If set to `true` it is the equivalent of ``--daemon``.
* ``CERTDEPLOY_SERVER_CONFIG`` - The path to the server config file. Equivalent to ``--config``.
* ``CERTDEPLOY_LOG_LEVEL`` - The log level. Equivalent to ``--log-level``.
* ``CERTDEPOLY_PUSH_ONLY`` - If set to `true` it is the equivalent of ``--push``.

#### Hook Environment Variables
The hook (``certdeploy-server`` when it's run by Certbot) expects the following environmental variables from Certbot in addition to the optional ``CERTDEPLOY_SERVER_CONFIG`` and ``CERTDEPLOY_LOG_LEVEL`` as described above.
* ``RENEWED_LINEAGE`` - The "lineage" or path to the renewed certs.
* ``RENEWED_DOMAINS`` - A space separated list of domains associated to the renewed certs.

### Configuration

#### Server Settings
* `client_configs` - A list of [client connection settings](#client-connection-settings).
* `privkey_filename` - The path to the CertDeploy server private key file.
* `fail_fast` (optional) - Stop on the first failed action. Defaults to `false`.
* `log_level` (optional) - The logging level. Options are ``DEBUG``, ``INFO``, ``WARNING``, ``ERROR``, ``CRITICAL``. Defaults to ``ERROR``.

The following are daemon specific configs.
* `renew_every` (optional) - The interval count to multiply `renew_unit` by. This must be a positive integer. The default is 1.
* `renew_unit` (optional) - The interval unit to check for new certs. This can be `minute`, `day`, `week`, or a weekday. Defaults to `day`.
* `renew_at` (optional) - The time of day to check for new certs. Formatted ``HH:MM``. Defaults to ``null`` which is equivalent to the current time.
* `renew_exec` (optional) - The path of the `certbot` executable. If for some reason `certbot` isn't in the `$PATH` this lets the full path be given. This is also useful for testing. The `tests/docker/mock/mock-certbot.sh` script in the repository can be mounted in the container and the path given with this option. That way settings can be tested without spamming [Let's Encrypt](https://letsencrypt.org/).
* `renew_args` (optional) - A list of arguments to pass to `certbot` when attempting to renew certs. Defaults to ``['renew']``.
* `push_mode` (optional) - The mode used to push certs to clients. This must be `serial` or `parallel`. Defaults to `serial`.
* `push_interval` (optional) - The number of seconds to wait between pushing to clients. This must be a positive integer or `0`. 0 disables the delay. Defaults to `0`.
* `push_retries` (optional) - The number of times to retry pushing certs to clients. This must be a positive integer or `0`. `0` disables retries. Defaults to `1` (1 initial attempt and one retry). This can be overridden on a client by client basis.
* `push_retry_interval` (optional) - The delay in seconds between retrying to push certs to clients. This must be an positive integer or `0`. 0 disables the delay between retries. Defaults to `30`.
* `join_timeout` (optional) - The number of seconds to wait while joining push threads. This must be a positive number or ``null``. ``null`` disables the timeout. Defaults to `None`. Set this to help identify the cause of hung pushes.
* `queue_dir` (optional) - The directory where the queue and the lock file will be stored. Defaults to ``/var/run/certdeploy``.


##### Scheduling Examples
* The default behavior is to try to renew once a day which is equivalent to the following.
    ```yaml
    renew_every: 1
    renew_unit: day
    renew_at: null
    ```
* To try to renew certs every other day at 3pm use the following.
    ```yaml
    renew_every: 2
    # `day` is the default for `renew_unit` so this can be left out if you want.
    renew_unit: day
    renew_at: 15:00
    ```
* To try to renew certs every Monday and you don't care about the time use the following.
    ```yaml
    renew_unit: monday
    ```


##### Push Retry Examples
* Wait 30 seconds between initial attempts to push to clients.
    ```yaml
    push_interval: 30
    ```
* Retry pushing to clients after an hour (3600 seconds).
    ```yaml
    push_retry_interval: 3600
    ```
* Retry pushing to clients after an hour and retry every hour 12 times.
    ```yaml
    push_retry_interval: 3600
    push_retries: 12
    ```


#### Client Connection Settings
* `address` - The client address (IP address or hostname).
* `domains` - A list of domains that this client needs certs for.
* `port` (optional) - The remote port of either an ssh server on the client or the CertDeploy client. Defaults to 22.
* `username` (optional) - The remote username to login to the ssh server or CertDeploy client with. Defaults to `certdeploy`.
* `pubkey` (optional) - The text of the client's public key. If the client is a regular SSH server remember to grab the SSH server's pubkey not the user's pubkey.
* `path` (optional) - The directory on the remote system where the CertDeploy client will look for new certs. Defaults to `/var/cache/certdeploy`. If set to ``null`` or an empty string the base path for the client will be used. This will be the configured `source` path on the client daemon or the home directory if the client is relying on the host system for SFTP.  This directory should only be readable by the CertDeploy user on the client since it will have TLS certs hanging around.
* `needs_chain` (optional) - If this is `true` the `chain.pem` from the relevant lineages will be copied to this client. Defaults to `false`.
* `needs_fullchain` (optional) - If this is `true` the `fullchain.pem` from the relevant lineages will be copied to this client. Defaults to `true`.
* `needs_privkey` (optional) - If this is `true` the `privkey.pem` from the relevant lineages will be copied to this client. Defaults to `true`.
* `push_retries` (optional) - The number of times to retry connecting to this client. This must be a positive integer or `0` if set. If set, it overrides the server's `push_retries` value for this client. `0` will cause the server to only try to push once (no retries). Defaults to ``null``.
* `push_retry_interval` (optional) - The interval in seconds to wait between retries for this client. This must be a positive integer or `0` if set. If set, it overrides the server's `push_retry_interval` value for this client. Defaults to ``null``.


##### Client Connection Examples
* Override the push retries and retry interval for just one client.
    ```yaml
    client_configs:
      - address: 1.2.3.4
        pubkey: ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIP+H3Nk/9uSa7LHNt8fvCPKKkNFnVE5SGC5tnthf6/OK
        domains:
          - example.com
        push_retries: 42
        push_retry_interval: 3600
      - address: 5.6.7.8
        pubkey: ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIEuhX3Q690lnBhpfGHOs0j4CuCxE3E3jekWehvHRmVKt
        domains:
          - example.net
    ```

#### Examples

##### Simple
A single client and private key. This will work in any of the server modes.
```yaml
---
privkey_filename: /etc/certdeploy/server_key
client_configs:
  - address: 1.2.3.4
    pubkey: ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIP+H3Nk/9uSa7LHNt8fvCPKKkNFnVE5SGC5tnthf6/OK
    domains:
      - example.com
```

##### Daemon
This can be given to `certdeploy-server` along with the `--daemon` option or as part of the [docker image](https://hub.docker.com/r/haxwithaxe/certdeploy-server) to run `certbot renew` every Monday at 9:00AM and deploy new certs for `example.com` to `1.2.3.4`.
```yaml
---
privkey_filename: /etc/certdeploy/server_key
renew_every: monday
renew_at: 09:00
client_configs:
  - address: 1.2.3.4
    pubkey: ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIP+H3Nk/9uSa7LHNt8fvCPKKkNFnVE5SGC5tnthf6/OK
    domains:
      - example.com
```

#### Server Security Considerations
When run as a script (`--renew`) or daemon outside of docker it's expected that the CertDeploy server will run as root or a user that has permission to run ``certbot renew``. Because it can run arbitrary code (via the `renew_exec` and `renew_args` configs) and distributes your TLS certs, it is very strongly recommended that the config file is globally read only or readable only by the user running the server, and writable only by root or at most only by the user that runs the server. Similarly (but less so) the push queue can be used to force the server to push certs or files that are where the given lineage should be. Putting the queue file in a place where other users can get to it doesn't directly create a security hole but it can be combined with other potential problems to distribute or exfiltrate data.

### Installation
The recommended way to use the server is to have it running in a docker container. The [server image](https://hub.docker.com/r/haxwithaxe/certdeploy-server) has Certbot baked in and automatically runs `certbot renew` on a schedule.

#### Docker
1. Create a directory to put the configs in and enter it. For example `mkdir conf && cd conf`.
1. Generate server key pair `ssh-keygen -t ed25519 -f server_key` Don't enter a password. CertDeploy doesn't support password files.
1. Create a `server.yml` with the clients. For now we'll assume you have the pubkey for the first client.
    ```yaml
    ---
    private_key_file: /etc/certdeploy/server_key
    client_configs:
      - address: <your client ip or hostname>
        pubkey: <your client's pubkey without the comment>
        domains:
          - <the domain name that this client needs certs for>
    check_renew:
      every: week
    ```
1. Install the docker container.
    ```
    docker run -d -v $(pwd)/conf:/etc/certdeploy -v /etc/letsencrypt:/etc/letsencrypt haxwithaxe/certdeploy-server
    ```
    Where ``./conf`` is a directory with a ``server.yml`` and an ED25519 key pair. If you don't see anything in the logs it's probably working fine. The default log level isn't verbose. You can add ``--env 'LOG_LEVEL=DEBUG'`` to get the firehose of output if you want to be certian it's working.

    Or with docker-compose with the following:
    ```yaml
    ---
    version: "3"

    services:
      certdeploy-server:
        image: haxwithaxe/certdeploy-server
        volumes:
          - "./conf:/etc/certdeploy"
          - "/etc/letsencrypt:/etc/letsencrypt"
    ```

#### Install in an existing system
1. Create a directory to put the configs in and enter it. For example `sudo mkdir /etc/certdeploy && cd /etc/certdeploy`.
1. Generate server key pair `sudo ssh-keygen -t ed25519 -f server_key` Don't enter a password. CertDeploy doesn't support password files.
1. Create a `server.yml` with the clients. For now we'll assume you have the pubkey for the first client.
    ```yaml
    ---
    private_key_file: /etc/certdeploy/server_key
    client_configs:
      - address: <your client ip or hostname>
        pubkey: <your client's pubkey without the comment>
        domains:
          - <the domain name that this client needs certs for>
    check_renew:
      every: week
    ```
1. Install CertDeploy `sudo pip install certdeploy`.
1. Install the CertDeploy CertBot hook.
    ```
    sudo ln -s /usr/local/bin/certdeploy-server /etc/letsencrypt/renewal-hooks/deploy/certdeploy-hook
    ```

## The Client

### Commandline Options
* `--config` - The path to the config file.
* `--daemon` - Run the daemon. Without this option the sync and update actions will run once and quit.
* `--log-level` - Set the log level to `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL`.

### Environment Variables
Commandline options override environment variables.
* ``CERTDEPLOY_CLIENT_DAEMON`` - If set to `true` it is the equivalent of ``--daemon``.
* ``CERTDEPLOY_CLIENT_CONFIG`` - The path to the client config file. Equivalent to ``--config``.
* ``CERTDEPLOY_LOG_LEVEL`` - The log level. Equivalent to ``--log-level``.

### Configuration

#### Generate client keypair
``ssh-keygen -t ed25519 -f client_key`` Don't enter a password. CertDeploy doesn't support password files.

#### Client settings
* `destination` - The path to dump the certs in. The certs will be placed in "lineage" directories within this directory as seen in ``/etc/letsencrypt/live`` in a certbot installation.
* `source` (optional) - The directory the server uploads the certs to. Defaults to ``/var/cache/certdeploy``.
* `sftpd` (optional) - The SFTP server settings. See below.
* `systemd_exec` (optional) - The path to the `systemctl` executable for restarting/reloading systemd units.
* `systemd_timeout` (optional) - The timeout in seconds for executing systemctl commands. Defaults to `null` (wait indefinitely).
* `docker_url` (optional) - The URL to the Docker API. Defaults to the local socket location.
* `update_sevices` - A list of definitions of services to reload/restart/run after deploying the certs.

##### Service Definitions
Each definition has a ``type`` key and one or more other keys. They are run in the order they are written in the config.
* Docker swarm services have a type of ``docker_service`` and can have a `name` key with a string value or a `filters` key with a dictionary of filters. See [Docker Services and Containers](#docker-services-and-containers).
*  Docker containers have a type of ``docker_container`` and can have a `name` key with a string value or a `filters` key with a dictionary of filters. See [Docker Services and Containers](#docker-services-and-containers).
* Systemd units  have a type of ``docker_service``, a `name` key with the unit name, and optionally an `action` key that can be either ``restart``or ``reload``. The default `action` is ``restart``. The `name` is the full unit names (with the unit type extension eg `nginx.service`). The value of `action` corresponds the systemctl arguments. See [Systemd Units](#systemd-units).
* Arbitrary scripts have the `type` ``script`` and a `name` key with the path of the script to execute. See [Scripts](#scripts).

This is an example of a hyper simple cron job or Systemd timer run client config that just moves the certs and doesn't restart any services.
```
destination: /etc/letsencrypt/live
```

In a case like this the certs are delivered via whatever ssh server is running on the client host and the `certdeploy-client` script is run as a user with permission to write to the destination directory (probably root). See the [this](#client-security-considerations) section for more info and security considerations.

#### Service settings

##### Scripts
The only option for scripts is `name` which is the path to the script.
`name` can be an absolute path, an executable in the system's ``$PATH``, or relative path (complicated). The path is evaluated in that order.
The relative path is relative to the current working directory which is different depending on how the client is being run.
```yaml
update_services:
  - type: script
    name: script_in_path.sh
  - type: script
    name: /path/to/script.sh
```

##### Systemd Units
The two config fields for each Systemd service are `name` and `action`. `action` can be `restart` or `reload` which correspond to the ``systemctl restart ...`` and ``systemctl reload ...`` commands. The default `action` is `restart`.
```yaml
update_services:
  - type: systemd
    name: nginx_or_whatever.service
  - type: systemd
    name: apache_or_whatever.service
    action: reload
```

##### Docker Services and Containers
The two config fields for each docker service or container are `name` and `filters`. Either name or filters can be given.
```yaml
update_services:
  - type: docker_service
    name: ingress_nginx
  - type: docker_service
    filters:
      label:
        - restart_on_cert_update
  - type: docker_container
    name: web_nginx_1
  - type: docker_container
    filters:
      name: web_traefik_1
```

The first of the example definitions is equivalent to the following:
```yaml
update_services:
  - type: docker_service
    filters:
      name: "^ingress_nginx$"
```
The name is automatically converted into a filter for the exact match if no filters are given.


#### Daemon specific settings
The `sftpd` section contains the settings for the SFTP server that accepts incoming certs from the CertDeploy server.
* `listen_port` (optional) - The port the CertDeploy client (SFTP server) listens on. Defaults to 22.
* listen_address` (optional) - The address the CertDeploy client (SFTP server) listens on. Defaults to listening on all interfaces.
* `username` (optional) - The username to require the CertDeploy server to login with. Defaults to `certdeploy`.
* `privkey_filename` - The path to the CertDeploy client (SFTP server) private key file. This is optional if `privkey` is given.
* `server_pubkey` - The text of the remote CertDeploy server (SFTP client) public key. This is optional if `server_pubkey_filename` is given and is overridden by `server_pubkey_filename`.
* `server_pubkey_filename` - The path to the remote CertDeploy server (SFTP client) public key file. This is optional if `server_pubkey` is given.
* `log_level` (optional) - The SFTP server log level. Defaults to `ERROR`. The valid values for this correspond to `logging` log levels.
* `log_filename` (optional) - The log file for the SFTP server. Defaults to ``/dev/stderr``.

Example snippet:
```yaml
sftpd:
  listen_port: 33774
  privkey_filename: /etc/certdeploy/client_key
  server_pubkey_filename: /etc/certdeploy/server_key.pub
```

#### Full Client Config Example
This config accepts new certs via SFTP into the default source directory. Moves them to the given destination directory. Then updates services. It restarts the nginx systemd service. It runs two scripts. It restarts a docker container. It force-updates docker swarm services based on two sets of filters. The updates aren't garanteed to be in any given order for now. The plan is to make the order something users set.
```yaml
---
destination: /etc/letsencrypt/live
update_services:
  - type: systemd
    name: nginx.service
  - type: script
    name: touch-flag-file.sh
  - type: script
    name: poke-the-custom-server.sh
  - type: docker_container
    name: internal_traefik_1
  - type: docker_service
    filters:
      label:
        - restart_on_cert_update
sftpd:
  listen_port: 33774
  privkey_filename: /etc/certdeploy/client_key
  server_pubkey_filename: /etc/certdeploy/server_key.pub
```

#### Client Security Considerations
When run as a script or daemon outside of docker it's expected that the CertDeploy client will run as root or a user that has permission to manage system services and docker. Because it can run arbitrary code (via the `script` service definitions) it is very strongly recommended that the config file and the update scripts are globally read only or readable only by the user that runs the client, and writable only by root or at most only the user that runs the client.

#### Installation

##### Cron Job
1. Create a config directory ``mkdir /etc/certdeploy``.
1. Create a config in ``/etc/certdeploy/client.yml``.
    ```yaml
    ---
    source: /var/cache/certdeploy
    destination: /etc/letsencrypt/live
    update_services:
      <put your service definitions here>
    ```
1. Ensure your `source` directory exists, is owned by the user the client is running as, and that only that user can read the contents of that directory.
1. Ensure the `destination` directory exists and is writable by the user the client is running as.
1. Add a cron entry that runs the ``certdeploy-client`` at whatever frequency you want.
    ```
    @daily                   /usr/bin/certdeploy-client
    ```

##### Daemon
1. Create a config directory ``mkdir /etc/certdeploy``.
1. Generate a client key pair ``ssh-keygen -t ed25519 -f /etc/certdeploy/client_key``. Don't enter a password. CertDeploy doesn't support password files.
1. Create a config in ``/etc/certdeploy/client.yml``.
    ```yaml
    ---
    source: /var/cache/certdeploy
    destination: /etc/letsencrypt/live
    update_services:
      <put your service definitions here>
    sftpd:
      listen_port: 33774
      privkey_filename: /etc/certdeploy/client_key
      server_pubkey_filename: /etc/certdeploy/server_key.pub
    ```
1. Ensure your `source` directory exists, is owned by the user the client is running as, and that only that user can read the contents of that directory.
1. Ensure the `destination` directory exists and is writable by the user the client is running as.
1. Start the daemon.
    ```sh
    certdeploy-client --daemon
    ```

##### Systemd Daemon
To run the client as a daemon with systemd the following example unit can be used.

/usr/local/lib/systemd/system/certdeploy-client.service
```
[Unit]
Description=Certdeploy Client Daemon
After=network.target

[Service]
Type=exec
ExecStart=/usr/local/bin/certdeploy-client --daemon

[Install]
WantedBy=multi-user.target
```

The instructions above for configuring the daemon apply here. Except for the "Start the daemon" step which should be replaced with the following commands.
```sh
systemctl enable certdeploy-client.service
systemctl start certdeploy-client.service
```

##### Systemd Timer
If only syncronization between directories is needed these two systemd units can be used to run the client as a script every hour.

/usr/local/lib/systemd/system/certdeploy-client.service
```
[Unit]
Description=Certdeploy Client
After=network.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/certdeploy-client
```

/usr/local/lib/systemd/system/certdeploy-client.timer
```
[Unit]
Description=CertDeploy Client Timer

[Timer]
OnUnitActiveSec=1h
Unit=certdeploy-client.service

[Install]
WantedBy=timers.target
```

The instructions in the "Cron Job" section above can be followed until the "Add a cron entry ..." step which should be replaced with the following.
```sh
systemctl enable certdeploy-client.timer
```

##### Docker
1. Create a config directory ``mkdir conf``.
1. Generate a client key pair ``ssh-keygen -t ed25519 -f conf/client_key``. Don't enter a password. CertDeploy doesn't support password files.
1. Create a config in ``conf/client.yml``.
    ```yaml
    ---
    source: /certdeploy/staging
    destination: /certdeploy/certs
    update_delay: 10m
    update_services:
      <put your service definitions here>
    sftpd:
      listen_port: 33774
      privkey_filename: /etc/certdeploy/client_key
      server_pubkey_filename: /etc/certdeploy/server_key.pub
    ```
1. Start the daemon.
    ```sh
    docker run -d -v $(pwd)/conf:/etc/certdeploy -v shared_certs:/certdeploy/certs haxwithaxe/certdeploy-client
    ```
    Where ``shared_certs`` is a docker volume shared with other containers that need access to the certs.

    Or with docker-compose using this:
    ```yaml
    ---
    version: "3"

    services:
      certdeploy-client:
        image: haxwithaxe/certdeploy-client
        volumes:
          - "./conf:/etc/certdeploy"
          - "shared_certs:/certdeploy/certs"
    ```

<!-- pyscaffold-notes -->

## Note

This project has been set up using PyScaffold 4.3. For details and usage
information on PyScaffold see https://pyscaffold.org/.
