#!/bin/sh

set -e

script="$0"
action="$1"
shift

case $action in
	renew)
		set -x
		echo TEST PASSED: got script=\"$script\" action=\"$action\" @=\"$@\"
		export RENEWED_LINEAGE=/etc/letsencrypt/live/example.com
		export RENEWED_DOMAINS="www.example.com example.com"
		/etc/letsencrypt/renewal-hooks/deploy/certdeploy-hook --log-level DEBUG && \
			echo HOOK PASSED: returned=$? || \
			echo HOOK FAILED: returned=$?
		exit 0
		;;
	*)
		echo TEST FAILED: Got: script=\"$script\" action=\"$action\" @=\"$@\"
		exit 255
		;;
esac
