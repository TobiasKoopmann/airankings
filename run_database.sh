#!/bin/bash
docker build -t ls6-staff-registry.informatik.uni-wuerzburg.de/koopmann/airankings-database:latest -f kubernetes/Dockerfile .
docker push ls6-staff-registry.informatik.uni-wuerzburg.de/koopmann/airankings-database:latest
kubectl -n koopmann delete job airankings-database
kubectl -n koopmann create -f kubernetes/airankings-database.yml
