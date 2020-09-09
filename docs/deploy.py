#!/usr/bin/env python3

from diagrams import Diagram, Cluster
from diagrams.aws.network import ELB
from diagrams.k8s.group import Namespace
from diagrams.k8s.compute import Deploy, Pod, ReplicaSet, Job
from diagrams.k8s.network import Service, Ingress
from diagrams.custom import Node, Custom
with Diagram('Refractr Deploy Flow'):
    with Cluster('ns: refractr'):
        deploy = Deploy('refractr')
        pod = Pod('refractr')
        sets = [ReplicaSet(f'refractr{i+1}') for i in range(3)]
        job = Job('preinstall-hook')
        cm = Custom('cert-manager', 'cert-manager-icon.png')

        deploy >> pod >> sets
        deploy >> job >> cm
