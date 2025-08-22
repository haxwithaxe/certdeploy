#!/bin/bash
# Publish the latest build as the current git tag or the value of the
#   environment variable $TAG

set -e

DEST_IMAGE_PREFIX="haxwithaxe/certdeploy"
ALT_DEST_IMAGE_PREFIX="ghcr.io/$DEST_IMAGE_PREFIX"
SRC_IMAGE_PREFIX="certdeploy"
TAG=${1:-${TAG:-$(git tag --points-at HEAD)}}

if [[ -z $TAG ]]; then
	echo No tag set. Either set the \$TAG environment variable or add a tag to HEAD. 1>&2
	exit 1
fi

echo Tagging ${SRC_IMAGE_PREFIX}-server as $TAG
if [[ "$TAG" != *"-"* ]]; then
	docker image tag ${SRC_IMAGE_PREFIX}-server:latest ${DEST_IMAGE_PREFIX}-server:latest
	docker image tag ${SRC_IMAGE_PREFIX}-server:latest ${ALT_DEST_IMAGE_PREFIX}-server:latest
fi
docker image tag ${SRC_IMAGE_PREFIX}-server:latest ${DEST_IMAGE_PREFIX}-server:$TAG
docker image tag ${SRC_IMAGE_PREFIX}-server:latest ${ALT_DEST_IMAGE_PREFIX}-server:$TAG
echo Pushing ${DEST_IMAGE_PREFIX}-server latest and $TAG
if [[ "$TAG" != *"-"* ]]; then
	docker image push ${DEST_IMAGE_PREFIX}-server:latest
	docker image push ${ALT_DEST_IMAGE_PREFIX}-server:latest
fi
docker image push ${DEST_IMAGE_PREFIX}-server:$TAG
docker image push ${ALT_DEST_IMAGE_PREFIX}-server:$TAG

echo Tagging ${SRC_IMAGE_PREFIX}-client as $TAG
if [[ "$TAG" != *"-"* ]]; then
	docker image tag ${SRC_IMAGE_PREFIX}-client:latest ${DEST_IMAGE_PREFIX}-client:latest
	docker image tag ${SRC_IMAGE_PREFIX}-client:latest ${ALT_DEST_IMAGE_PREFIX}-client:latest
fi
docker image tag ${SRC_IMAGE_PREFIX}-client:latest ${DEST_IMAGE_PREFIX}-client:$TAG
docker image tag ${SRC_IMAGE_PREFIX}-client:latest ${ALT_DEST_IMAGE_PREFIX}-client:$TAG
echo Pushing ${DEST_IMAGE_PREFIX}-client latest and $TAG
if [[ "$TAG" != *"-"* ]]; then
	docker image push ${DEST_IMAGE_PREFIX}-client:latest
	docker image push ${ALT_DEST_IMAGE_PREFIX}-client:latest
fi
docker image push ${DEST_IMAGE_PREFIX}-client:$TAG
docker image push ${ALT_DEST_IMAGE_PREFIX}-client:$TAG
