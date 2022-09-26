#!/bin/sh

# Make sure the hook is in place even if the directory has been mounted from elsewhere
mkdir -p /etc/letsencrypt/renewal-hooks/deploy
ln -sf /usr/local/bin/certdeploy-server /etc/letsencrypt/renewal-hooks/deploy/certdeploy-hook

if [[ "$CERTDEPLOY_RENEW_ONLY" == "true" ]]; then
	certdeploy-server --renew
elif [[ -n "$1" ]]; then
	if [[ "$1" == "certdeploy-server" ]]; then
		# This case is mostly for testing
		$@
	else
		# Emulate the certbot docker image interface as much as possible.
		certbot $@
	fi
else
	certdeploy-server --daemon
fi
