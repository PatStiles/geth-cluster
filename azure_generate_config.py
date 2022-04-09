#! /usr/bin/python3

''' Helper scripts to generate a config on the Azure cluster '''

from time import sleep
from math import ceil

import argparse

from azure.identity import AzureCliCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.network import NetworkManagementClient

from azure_config import load_azure_credentials, GROUP_NAME, NETWORK_NAME, SUBNET_NAME, LOCATION, IMAGE

CREATE_GROUP = False

conf = load_azure_credentials()

compute_client = ComputeManagementClient(credential=AzureCliCredential(), subscription_id=conf["SUBSCRIPTION_ID"])
resource_client = ResourceManagementClient(credential=AzureCliCredential(), subscription_id=conf["SUBSCRIPTION_ID"])
network_client = NetworkManagementClient(credential=AzureCliCredential(), subscription_id=conf["SUBSCRIPTION_ID"])

subnet = network_client.subnets.begin_create_or_update(
        GROUP_NAME,
        NETWORK_NAME,
        SUBNET_NAME,
        {'address_prefix': '10.0.0.0/24'}
    ).result()

def _create_vm(name, vm_type):
    ifname = f"{name}-netif"
    ipname = f"{name}-pubip"

    pub_ip = network_client.public_ip_addresses.begin_create_or_update(
        GROUP_NAME, ipname, {
            'location': LOCATION,
            'public_ip_allocation_method': 'dynamic'
        }
    ).result()

    netif = network_client.network_interfaces.begin_create_or_update(
        GROUP_NAME,
        ifname,
        {
            'location': LOCATION,
            'ip_configurations': [{
                'name': ifname,
                'subnet': {
                    'id': subnet.id
                },
                'public_ip_address' : {
                    'id': pub_ip.id
                }
            }]
        }
    ).result()

    vm_op = compute_client.virtual_machines.begin_create_or_update(
        GROUP_NAME,
        name,
        {
          "location": "eastus",
          "hardware_profile": {
            "vm_size": vm_type
          },
          "storage_profile": {
            "image_reference": {
              "id": IMAGE
             },
            "os_disk": {
              "caching": "ReadWrite",
              "managed_disk": {
                "storage_account_type": "Standard_LRS"
              },
              "name": f"{name}-disk",
              "create_option": "FromImage"
            },
            "data_disks": []
          },
          "os_profile": {
            "admin_username": "kai",
            "admin_password": "usesshinsteadofpw_47",
            "computer_name": name.replace('_', '-'),
            "linux_configuration": {}
          },
          "network_profile": {
            "network_interfaces": [
              {
                "id": netif.id,
                "properties": {
                  "primary": True
                }
              }
            ]
          }
        }
    )

    ip_config = netif.ip_configurations[0]
    priv_ip = ip_config.private_ip_address

    while pub_ip.ip_address is None:
        sleep(1.0)
        pub_ip = network_client.public_ip_addresses.get(GROUP_NAME, ipname)

    return (vm_op, pub_ip.ip_address, priv_ip)

def _main():
    parser = argparse.ArgumentParser(description='update the cluster config')
    parser.add_argument('--num_geth_nodes', default=1, type=int)

    args = parser.parse_args()

    if CREATE_GROUP:
        resource_client.resource_groups.create_or_update(
                GROUP_NAME, {"location": LOCATION}
            )

        network_client.virtual_networks.begin_create_or_update(
                GROUP_NAME,
                NETWORK_NAME,
                {
                    'location': "eastus", 'address_space': {
                        'address_prefixes': ['10.0.0.0/16']
                    }
                }
            ).result()

    print("# Creating or starting virtual machines")
    ops = []

    clients = []
    data_pods = []
    blockchain = []

    num_data_pod_machines = args.num_geth_nodes
    num_client_machines = max(int(ceil(num_data_pod_machines / 2)), 1)

    for pos in range(num_client_machines):
        vm_op, pub_ip, priv_ip = _create_vm(f"dp_client{pos}", "Standard_DS1_v2")
        ops.append(vm_op)
        clients.append(f'["{pub_ip}", "{priv_ip}"]')

    print("Waiting...")

    for (pos, vm_op) in enumerate(ops):
        vm_op.result()

    print("Done")

    print("# Generating cluster file")
    with open('cluster.toml', 'w', encoding='utf-8') as config_file:
        config_file.write(f"clients = [{', '.join(clients)}]")
        config_file.write(f"servers = [{', '.join(data_pods)}]")
        config_file.write(f"blockchain = [{', '.join(blockchain)}]")

if __name__ == "__main__":
    _main()
