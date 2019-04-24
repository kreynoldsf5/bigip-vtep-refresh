#!/usr/bin/python
import requests
from requests.auth import HTTPBasicAuth
import json
import os
import sys
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import urllib3
urllib3.disable_warnings()
from pprint import pprint


def main():
    ################################
    # Find BIG-IP VTEP MAC Address #
    ################################
    bipMGMT = os.getenv('BIP')
    bipUser = os.getenv('BIPUSER')
    bipPass = os.getenv('BIPPASS')
    bipPodCIDR = os.getenv('BIPPODCIDR')
    bipName = os.getenv('BIPNAME')
    bipFlanPIP = os.getenv('BIPFLANPIP')

    try:
        br = requests.get('https://{}/mgmt/tm/net/tunnels/tunnel/~Common~flannel_vxlan/stats?options=all-properties'.format(bipMGMT), verify=False, auth=HTTPBasicAuth(bipUser, bipPass))
        br.raise_for_status()
    except requests.exceptions.HTTPError as err:
        pprint(err)
        sys.exit(1)
    except requests.exceptions.RequestException as err:
        pprint(err)
        sys.exit(1)
    try:
        vtepMAC = br.json()['entries']['https://localhost/mgmt/tm/net/tunnels/tunnel/~Common~flannel_vxlan/~Common~flannel_vxlan/stats']['nestedStats']['entries']['macAddr']['description']
    except json.decoder.JSONDecodeError as err:
        pprint(err)
        sys.exit(1)
    
    ##################
    #Create K8s Node #
    ##################
    config.load_incluster_config()
    api_instance = client.CoreV1Api()
    body = client.V1Node()
    body.spec = client.V1NodeSpec(pod_cidr=bipPodCIDR)
    body.metadata = client.V1ObjectMeta(name=bipName, annotations={"flannel.alpha.coreos.com/backend-data": {"VtepMAC": vtepMAC}, "flannel.alpha.coreos.com/public-ip": bipFlanPIP, "flannel.alpha.coreos.com/backend-type": "vxlan", "flannel.alpha.coreos.com/kube-subnet-manager": "true"})

    try: 
        api_response = api_instance.create_node(body, pretty=True)
        pprint(api_response)
        sys.exit(0)
    except ApiException as e:
        print("Exception when calling CoreV1Api->create_node: %s\n" % e)
        sys.exit(1)

if __name__ == '__main__':
    main()
