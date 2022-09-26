#!/bin/sh


script="$0"
action="$1"
shift


handle_service() {
	local service=$1
	shift
	if [[ -z "$service" ]]; then
		echo TEST FAILED: No service given Got: "$script $action $service $@" | tee /dev/stderr
		exit 255
	fi
	if ( echo $service | grep -iq fail ); then
		echo SYSTEMCTL SUCCESS: Exiting non-zero: Got: "$script $action $service ---extra-> \"$@\"" | tee /dev/stderr
		exit 1
	else
		echo SYSTEMCTL SUCCESS: Got: "$script $action $service ---extra-> \"$@\"" | tee /dev/stderr
		exit 0
	fi
}


case $action in
	restart|reload)
		handle_service $@
		exit 0
		;;
	*)
		echo TEST FAILED: Got: "$script $action $@" | tee /dev/stderr
		exit 255
		;;
esac
