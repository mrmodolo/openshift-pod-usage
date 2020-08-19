# Pod Usage

docker build -t modolo/openshift-pod-usage:latest .

docker run --rm -p 8000:8000 \
-e "NAMESPACES=..." \
-e "OPENSHIFT_SERVER=https://..." \
-e "OPENSHIFT_TOKEN=..." \
-e "WAIT_TIME_SECONDS=300" modolo/openshift-resources:latest


