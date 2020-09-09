#!/usr/bin/env python3

from diagrams import Diagram, Cluster
from diagrams.aws.network import ELB
from diagrams.k8s.group import Namespace
from diagrams.k8s.compute import Deploy, Pod, ReplicaSet, Job
from diagrams.k8s.network import Service, Ingress
from diagrams.custom import Node, Custom
with Diagram('Refractr Traffic Flow'):
    elb = ELB('AWS ELB')
    with Cluster('ns: refractr'):
        ingress = Ingress('Nginx Ingress')
        pod = Pod('refractr')
        sets = [ReplicaSet(f'refractr{i+1}') for i in range(3)]
        cm = Custom('cert-manager', 'cert-manager-icon.png')

        elb >> ingress >> cm >> pod >> sets
