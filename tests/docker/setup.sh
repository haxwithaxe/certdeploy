#!/bin/bash
# Run this once before running run.sh
# This script generates keys for testing, installs the keys in the appropriate
#   directories and pubkeys in client connection configs, and preps the
#   fail_fast client configs.

DOCKER_TEST_ROOT="$(dirname "$0")"

set -ex

# Remove test output cruft
sudo rm -rf tests/docker/server/etc-letsencrypt/renewal-hooks/

# Make the test output directories
mkdir -p ${DOCKER_TEST_ROOT}/output/{client_certs,systemd_certs}
# Make sure they are empty
sudo rm -rf ${DOCKER_TEST_ROOT}/output/*/*


# Generate client key pair (the regular and systemd clients share keys)
if ! [ -f  "${DOCKER_TEST_ROOT}/client/client_key" ]; then
	ssh-keygen -t ed25519 -f "${DOCKER_TEST_ROOT}/client/client_key" <<< ''
fi
# Generate server key pair
if ! [ -f  "${DOCKER_TEST_ROOT}/server/server_key" ]; then
	ssh-keygen -t ed25519 -f "${DOCKER_TEST_ROOT}/server/server_key" <<< ''
	# Copy the server pubkey to the client config dir
	cp "${DOCKER_TEST_ROOT}/server/server_key.pub" "${DOCKER_TEST_ROOT}/client/server_key.pub"
fi
# Grab the client pubkey without the message
client_pubkey=$(cat "${DOCKER_TEST_ROOT}/client/client_key.pub"|sed 's/ [a-zA-Z0-9._-]\+@[a-zA-Z0-9._-]\+$//')
echo Found client pubkey $client_pubkey
# Put the client pubkey in the server config
sed -i 's/    pubkey:.*/    pubkey: '"${client_pubkey//\//\\\/}"'/' "${DOCKER_TEST_ROOT}/server/server.yml"


echo Setup Fail Fast Client Configs
mkdir -p ${DOCKER_TEST_ROOT}/client/fail_fast
for conf in ${DOCKER_TEST_ROOT}/client/*.yml; do
	cp $conf ${DOCKER_TEST_ROOT}/client/fail_fast/
	echo "fail_fast: true" >> "${DOCKER_TEST_ROOT}/client/fail_fast/$(basename "$conf")"
	# Uncomment fail_fast test configs
	sed -i 's/#fail_fast-test//'  "${DOCKER_TEST_ROOT}/client/fail_fast/$(basename "$conf")"
done
