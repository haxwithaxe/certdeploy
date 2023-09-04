#!/bin/bash

set -e


CONTEXT="$(dirname "$(dirname "$(realpath "$0")")")"


build_client() {
	docker build \
		--progress plain \
		-f $CONTEXT/docker/client/Dockerfile \
		-t certdeploy-client:latest \
		$@ \
		$CONTEXT
}


build_server() {
	docker build \
		--progress plain \
		-f $CONTEXT/docker/server/Dockerfile \
		-t certdeploy-server:latest \
		$@ \
		$CONTEXT
}


case $1 in
	server)
		shift
		build_server $@
		exit 0
		;;
	client)
		shift
		build_client $@
		exit 0
		;;
	*)
		build_client $@ &
		build_server $@
		wait
		;;
esac
