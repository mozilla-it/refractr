#!/usr/bin/env python3

<<<<<<< HEAD
import os
import sys

import yaml
from google.cloud import certificate_manager_v1


def refractr_create_dns_authorization(hostname, id):
=======
from google.cloud import certificate_manager_v1
import yaml
import os
import sys

def refractr_create_dns_authorization(hostname,id):
>>>>>>> 300be44 (add_script_to_create_certs)
    # Create a client
    client = certificate_manager_v1.CertificateManagerClient()

    # Initialize request argument(s)
    dns_authorization = certificate_manager_v1.DnsAuthorization()
    dns_authorization.domain = hostname
    dns_authorization.description = "created by script"

    request = certificate_manager_v1.CreateDnsAuthorizationRequest(
        parent=f"projects/{PROJECT_ID}/locations/global",
        dns_authorization_id=id,
        dns_authorization=dns_authorization,
    )

    # Make the request
    operation = client.create_dns_authorization(request=request)

    print("Waiting for operation to complete...")

    response = operation.result()

    # Handle the response
    print(response)
    return response.name


<<<<<<< HEAD
def refractr_create_certificate(hostname, certname, dns_auth=None):
=======
def refractr_create_certificate(hostname,certname, dns_auth=None):
>>>>>>> 300be44 (add_script_to_create_certs)
    # Create a client
    client = certificate_manager_v1.CertificateManagerClient()
    certificate = certificate_manager_v1.Certificate()
    certificate.managed.domains = hostname
    certificate.managed.dns_authorizations = dns_auth
    certificate.name = f"projects/{PROJECT_ID}/locations/global/certificates/{certname}"

    # Initialize request argument(s)
    request = certificate_manager_v1.CreateCertificateRequest(
<<<<<<< HEAD
        parent=f"projects/{PROJECT_ID}/locations/global",
        certificate_id=certname,
        certificate=certificate,
=======
        parent= f"projects/{PROJECT_ID}/locations/global",
        certificate_id= certname,
        certificate = certificate,
>>>>>>> 300be44 (add_script_to_create_certs)
    )

    # Make the request
    operation = client.create_certificate(request=request)

    print("Waiting for operation to complete...")

    response = operation.result()

    # Handle the response
    print(response)


<<<<<<< HEAD
def refractr_create_certificate_map_entry(hostname, certname, map_entry_id):
=======
def refractr_create_certificate_map_entry(hostname,certname,map_entry_id):
>>>>>>> 300be44 (add_script_to_create_certs)
    # Create a client
    client = certificate_manager_v1.CertificateManagerClient()

    # Initialize request argument(s)
    certificate_map_entry = certificate_manager_v1.CertificateMapEntry()
    certificate_map_entry.hostname = hostname
<<<<<<< HEAD
    certificate_map_entry.certificates = [
        f"projects/{PROJECT_ID}/locations/global/certificates/{certname}"
    ]
=======
    certificate_map_entry.certificates = [f"projects/{PROJECT_ID}/locations/global/certificates/{certname}"]
>>>>>>> 300be44 (add_script_to_create_certs)

    request = certificate_manager_v1.CreateCertificateMapEntryRequest(
        parent=f"projects/{PROJECT_ID}/locations/global/certificateMaps/{CERT_MAP}",
        certificate_map_entry_id=map_entry_id,
        certificate_map_entry=certificate_map_entry,
    )

    # Make the request
    operation = client.create_certificate_map_entry(request=request)

    print("Waiting for operation to complete...")

    response = operation.result()

    # Handle the response
    print(response)


def refractr_list_certificate_map_entries():
    # Create a client
    client = certificate_manager_v1.CertificateManagerClient()

    # Initialize request argument(s)
    request = certificate_manager_v1.ListCertificateMapEntriesRequest(
        parent=f"projects/{PROJECT_ID}/locations/global/certificateMaps/{CERT_MAP}",
    )

    # Make the request
    page_result = client.list_certificate_map_entries(request=request)

    # Handle the response

    certs = []

<<<<<<< HEAD
=======

>>>>>>> 300be44 (add_script_to_create_certs)
    for response in page_result:
        print(response.hostname)
        certs.append(response.hostname)

<<<<<<< HEAD
    return certs
=======
    return(certs)
>>>>>>> 300be44 (add_script_to_create_certs)


PROJECT_ID = sys.argv[1]
CERT_MAP = sys.argv[2]

# get the list of the already created certificates.
existing_certs = refractr_list_certificate_map_entries()


# read the content of the cert manager input
<<<<<<< HEAD
with open("../image/certificate_manager_input.yaml", "r") as f:
=======
with open('test_list.yaml', 'r') as f:
>>>>>>> 300be44 (add_script_to_create_certs)
    doc = yaml.safe_load(f)

# iterate over the cert list not created .
for cert in doc:
<<<<<<< HEAD
    if cert["hostname"] not in existing_certs:
        certname = cert["hostname"].replace(".", "-")
        if "additional_domains" in cert.keys():
=======
    if cert['hostname'] not in existing_certs:
        certname = cert['hostname'].replace('.','-')
        if 'additional_domains' in cert.keys():

>>>>>>> 300be44 (add_script_to_create_certs)
            # generate the random id
            random_id = os.urandom(8).hex()

            # the dns authorization id
<<<<<<< HEAD
            id = f"{cert['hostname'].replace('.','-')}-dns-auth-{random_id}"

            # creating the dns authorization for additional domains and storing the DNS auth in a variable
            dns_auth = [f"{refractr_create_dns_authorization(cert['hostname'],id)}"]

            managed_domains = []
            managed_domains = [cert["hostname"], cert["additional_domains"][0]]
            # create certificate and passing the dnsAuthorization
            refractr_create_certificate(
                hostname=managed_domains, certname=certname, dns_auth=dns_auth
            )

            map_entry_id = f"refractr-prod-prod--{random_id}"
            refractr_create_certificate_map_entry(
                hostname=cert["hostname"], certname=certname, map_entry_id=map_entry_id
            )

        else:
            # create certificate for domains with no wildcards.
            managed_domain = [f"{cert['hostname']}"]
            refractr_create_certificate(hostname=managed_domain, certname=certname)
=======
            id =  f'{cert['hostname'].replace('.','-')}-dns-auth-{random_id}'

            # creating the dns authorization for additional domains and storing the DNS auth in a variable
            dns_auth= [f"{refractr_create_dns_authorization(cert['hostname'],id)}"]

            managed_domains = []
            managed_domains = [cert["hostname"] , cert["additional_domains"][0]]
            # create certificate and passing the dnsAuthorization
            refractr_create_certificate(hostname=managed_domains,certname=certname,dns_auth=dns_auth)

            map_entry_id = f"refractr-prod-prod--{random_id}"
            refractr_create_certificate_map_entry(hostname=cert['hostname'],certname=certname,map_entry_id=map_entry_id)

        else:
            # create certificate for domains with no wildcards.
            print(cert['hostname'])
            managed_domain = [f"{cert['hostname']}"]
            refractr_create_certificate(hostname=managed_domain,certname=certname)
>>>>>>> 300be44 (add_script_to_create_certs)

            random_id = os.urandom(8).hex()
            # random map entry id
            map_entry_id = f"refractr-prod-prod--{random_id}"
            # create the map entry for the created certificate in the refractr certificate manager map.
<<<<<<< HEAD
            refractr_create_certificate_map_entry(
                hostname=cert["hostname"], certname=certname, map_entry_id=map_entry_id
            )
=======
            refractr_create_certificate_map_entry(hostname=cert['hostname'],certname=certname,map_entry_id=map_entry_id)















>>>>>>> 300be44 (add_script_to_create_certs)
