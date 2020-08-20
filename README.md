# Pod Usage

docker build -t modolo/openshift-pod-usage:latest .

docker run --rm -p 8000:8000 \
-e "NAMESPACES=..." \
-e "OPENSHIFT_SERVER=..." \
-e "OPENSHIFT_TOKEN=..." \
-e "WAIT_TIME_SECONDS=300" modolo/openshift-resources:latest

[CHAPTER 9. DEPLOYMENTS](https://access.redhat.com/documentation/en-us/openshift_container_platform/3.11/html/developer_guide/deployments)

[Running a Pod with a Different Service Account](https://docs.openshift.com/enterprise/3.2/dev_guide/deployments.html#run-pod-with-different-service-account)

[Using a Service Account’s Credentials Inside a Container](https://docs.openshift.com/container-platform/3.6/dev_guide/service_accounts.html)


