#!/bin/bash


set -e


SCRIPT_PATH=$(realpath $0)
DOCKER_TEST_ROOT=$(dirname $SCRIPT_PATH)
DOCKER_SWARM_STACK_NAME=certdeploytest


header() {
	local level=$1
	shift
	printf '\033[0;33m'
	for i in $(seq $level); do
		printf "#"
	done
	printf '\033[1;34m'
	printf " $@"
	printf '\033[0m\n'
}


success_message() {
	printf '\033[0;32m'
	printf "$@"
	printf '\033[0m\n\n'
}


error_message() {
	printf '\033[0;31m' >&2
	printf "$@" >&2
	printf '\033[0m\n\n' >&2
}


fail_if_output() {
	set +x
	local pattern="$1"
	output=$(cat -)
	if (printf "$output" | grep -q "$pattern"); then
		error_message "Failed: Got \"$pattern\""
		printf "${output}\n\n"
		set -x
		exit 1
	fi
	printf "${output}\n\n"
	set -x
	return 0
}


pass_if_output() {
	set +x
	count=$2
	output=$(cat -)
	matches=$(printf "$output" | grep "$1" | wc -l)
	if [[ $count -eq $matches ]]; then
		success_message "Got \"$1\" $matches times ... Passed"
		printf "${output}\n\n"
		set -x
		return 0
	fi
	error_message "Failed: Found \"$1\" $matches times not $count"
	printf "${output}\n\n"
	set -x
	exit 1
}


docker_up_d() {
	set -x
	docker-compose up -d --force-recreate --remove-orphans $@ 2>&1 | \
		fail_if_output '... error'
	set +x
}


docker_up() {
	set -x
	docker-compose up --force-recreate --remove-orphans $@ 2>&1 | \
		fail_if_output '... error'
	set +x
}


teardown_debug_nobuild() {
	# Not printing a header to allow silent use.
	# Strip out debug and nobuild settings.
	sed -i '/^.*#NOBUILD_TESTING$/d' "$DOCKER_TEST_ROOT/docker-compose.yml"
	sed -i '/^.*#DEBUG_TESTING$/d' "$DOCKER_TEST_ROOT/docker-compose.yml"
}


teardown_test_env() {
	header 2 Teardown Testing Environment
	set -x
	docker-compose stop || true
	docker-compose rm --force || true
	set +x
}


test_simple_server_and_clients() {
	header 3 "Setup: Start clients"
	setup_docker_services ${DOCKER_TEST_ROOT}/stack.yml $DOCKER_SWARM_STACK_NAME
	docker_up_d docker_service_client docker_container_client script_client systemd_client hello
	header 4 "Wait for the containers to start: 40 seconds"
	sleep 40
	header 3 "Test: server"
	# Fails on any error
	docker_up server | \
		fail_if_output 'ERROR:certdeploy-server'
	success_message "Passed: Test: server"
	header 4 "Wait for the services to be updated: 40 seconds"
	sleep 40
	header 3 "Verify client behavior"
	header 4 "hello container uptime should be less than 40 seconds"
	# Only checking for less than a minute but ideally this should check for less
	#   than the wait time after the server is started
	set -x
	docker container ls --format '{{.Names}} {{.Status}}' --filter 'name=^hello$' | \
		pass_if_output 'seconds' 1
	set +x
	success_message "Passed: hello container uptime should be less than 40 seconds"
	header 4 "${DOCKER_SWARM_STACK_NAME}_hello service uptime should be less than 40 seconds"
	sleep 5 # Waiting a little more for the service to finish updating.
	set -x
	docker service ps \
		--filter 'desired-state=running' \
		--format '{{.Name}} {{.CurrentState}}' \
		"${DOCKER_SWARM_STACK_NAME}_hello" | \
		pass_if_output 'seconds ago' 1
	set +x
	success_message "Passed: ${DOCKER_SWARM_STACK_NAME}_hello service uptime should be less than 40 seconds"
	header 4 "Client logs should not have any error messages"
	# Fails on any error
	set -x
	docker-compose logs docker_service_client docker_container_client script_client systemd_client | \
		fail_if_output 'ERROR:certdeploy-client'
	set +x
	success_message "Passed: Client logs should not have any error messages"
}


test_certbot_passthrough_only() {
	header 3 "Test: certbot_passthrough_server"
	# /entrypoint.sh --help is called so checking for certbot --help text
	docker_up certbot_passthrough_server | \
		fail_if_output 'ERROR:certdeploy-server' | \
		pass_if_output 'certbot \[SUBCOMMAND\] \[options\] \[-d DOMAIN\] \[-d DOMAIN\]' 1
}


test_renew_only() {
	header 3 "Setup: Start clients"
	docker_up_d noop_client
	header 4 "Wait for the containers to start: 10 seconds"
	sleep 10  # Wait for the containers to start
	header 3 "Test: server"
	# Fails on any error
	docker_up renew_mock_certbot_server | \
		fail_if_output 'ERROR:certdeploy-server'
	header 4 "Wait for the services to be updated: 10 seconds"
	sleep 10  # Wait for the services to be updated
	# Check output
	header 3 "Verify client behavior"
	header 4 "Client logs should not have any error messages from the clients"
	# Fails on any error
	set -x
	docker-compose logs noop_client | \
		fail_if_output 'ERROR:certdeploy-client'
	set +x
}


test_fail_fast_daemon_mock_certbot_server() {
	header 3 "Test: fail fast daemon fails fast"
	# Expect one error message
	docker_up fail_fast_daemon_mock_certbot_server | \
		pass_if_output 'ERROR:certdeploy-server:CertDeployError: Failed to run `/bin/false renew`' 1
}


test_fail_fast_server() {
	header 3 "Test: fail fast server fails fast"
	# Expect one error message
	docker_up fail_fast_server | \
		pass_if_output 'ERROR:certdeploy-server:gaierror: \[Errno -2\] Name does not resolve' 1
}


teardown_docker_services() {
	set -x
	docker stack rm $1
	set +x
}


setup_docker_services() {
	header 2 Teardown Docker Services
	set -x
	docker stack deploy -c $1 $2
	set +x
}


_test_fail_fast_some_client() {
	local some_client=$1
	local error_message=$2
	header 3 "Test client: fail_fast for $some_client"
	header 4 "Start $some_client"
	docker_up_d $some_client
	header 4 "Start the server"
	docker_up fail_fast_runner_server
	sleep 20
	header 4 "Verify the $some_client container is gone"
	# Fail if the container is found
	local name=$(docker ps --format '{{.Names}}' --filter "name=$some_client")
	[[ -z "$name" ]]
	header 4 "Verify only one error in $some_client log"
	set -x
	# Expect one error message
	docker-compose logs $some_client | \
		pass_if_output "$error_message" 1
	set +x
	success_message "Passed: Test client: fail_fast for $some_client"
	echo
	teardown_test_env 2> /dev/null
}


test_all() {
	header 2 "Test server: entrypoint acts like certbot image"
	test_certbot_passthrough_only
	success_message "Passed: Test server: entrypoint acts like certbot image"
	teardown_test_env 2> /dev/null

	header 2 "Test server: renew certs (mock certbot)"
	test_renew_only
	success_message "Passed: Test server: renew certs (mock certbot)"
	teardown_test_env 2> /dev/null

	header 2 "Test server: fail fast as command"
	test_fail_fast_server
	success_message "Passed: Test server: fail fast as command"
	teardown_test_env 2> /dev/null

	header 2 "Test server: fail fast daemon (also renew)"
	# This causes a failure in a way that requires both the daemon code and
	#   renew code to fail fast
	test_fail_fast_daemon_mock_certbot_server
	success_message "Passed: Test server: fail fast daemon (also renew)"
	teardown_test_env 2> /dev/null

	header 2 "Test mixed: simple server and clients"
	test_simple_server_and_clients
	success_message "Passed: Test mixed: simple server and clients"
	teardown_test_env 2> /dev/null

	header 2 "Test clients: fail fast"
	_test_fail_fast_some_client fail_fast_docker_container_client \
		'ERROR:certdeploy-client:DockerContainerNotFound: DockerContainer no_such_container failed to update'
	_test_fail_fast_some_client fail_fast_docker_service_client \
		'ERROR:certdeploy-client:DockerServiceNotFound: DockerService nosuch_service failed to update'
	_test_fail_fast_some_client fail_fast_script_non_zero_client \
		'ERROR:certdeploy-client:ScriptError: Script /scripts/fail.sh failed to update:'
	_test_fail_fast_some_client fail_fast_systemd_client \
		'ERROR:certdeploy-client:SystemdError: SystemdUnit mock-fail-systemd.service'
	success_message "Passed: Test clients: fail fast"
	success_message "PASSED ALL TESTS!"
}


teardown_debug_nobuild
# Select a build mode
for arg in $@; do
	case $arg in
		nobuild)
			header 1 "Using nobuild mode"
			# Add volume entries pointing the image src directory to the repo
			sed -i '/^.*#NOBUILD_TESTING$/d' "$DOCKER_TEST_ROOT/docker-compose.yml"
			sed -i 's/volumes:$/&\n      - "..\/..\/src:\/certdeploy\/src\/src" #NOBUILD_TESTING/' "$DOCKER_TEST_ROOT/docker-compose.yml"
			;;
		debug)
			header 1 "Using debug mode"
			# Add environment variable to enable debug logging
			sed -i '/^.*#DEBUG_TESTING$/d' "$DOCKER_TEST_ROOT/docker-compose.yml"
			sed -i 's/environment:$/&\n      CERTDEPLOY_LOG_LEVEL: DEBUG  #DEBUG_TESTING/' "$DOCKER_TEST_ROOT/docker-compose.yml"
			;;
		teardown)
			header 2 "Restoring the docker-compose.yml"
			teardown_debug_nobuild
			teardown_test_env
			teardown_docker_services $DOCKER_SWARM_STACK_NAME || true
			exit 0
			;;
		help|-h|--help)
			echo "$0 [debug|nobuild|teardown]"
			echo "If no option is given tests are run without debug or nobuild settings."
			echo "Both debug and nobuild can be given at once to use them both."
			exit 1
			;;
	esac
done


pushd "$DOCKER_TEST_ROOT" > /dev/null

header 1 Prepare
set -x
# Remove test output cruft
sudo rm -rf ${DOCKER_TEST_ROOT}/server/etc-letsencrypt/renewal-hooks || true
sudo rm -rf ${DOCKER_TEST_ROOT}/output/* || true
set +x
# This can get into a weird state so it's easier to mess with it here than in
#   teardown_test_env(). If the swarm service doesn't start comment the line
#   below with a DEBUG or FIXME comment (so that the pre-commit catches it).
teardown_docker_services "$DOCKER_SWARM_STACK_NAME" || [ $? -eq 127 ]
# clear out any leftover state
teardown_test_env

header 1 Test
test_all
# Strip out the testing lines from docker-compose.yml on successful testing
teardown_debug_nobuild
teardown_docker_services "$DOCKER_SWARM_STACK_NAME" || [ $? -eq 127 ]

popd > /dev/null
