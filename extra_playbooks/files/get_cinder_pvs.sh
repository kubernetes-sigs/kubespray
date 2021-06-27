#!/bin/sh
kubectl get pv -o go-template --template='{{ range .items }}{{ $metadata := .metadata }}{{ with $value := index .metadata.annotations "pv.kubernetes.io/provisioned-by" }}{{ if eq $value "kubernetes.io/cinder" }}{{printf "%s\n" $metadata.name}}{{ end }}{{ end }}{{ end }}'
