#!/usr/bin/env python3
import os
import pynetbox
import requests  
import re
import json
from dotenv import load_dotenv
from jinja2 import Template                     


load_dotenv()
true_false = {
    'True': True,
    'False': False
}
netbox_url                  = os.environ['NETBOX_URL']
netbox_private_key          = os.environ['NETBOX_KEY']
netbox_token                = os.environ['NETBOX_TOKEN']
netbox_ssl_verify           = true_false.get(os.environ.get('NETBOX_SSL_VERIFY','True'),'True')
tf_file_template            = os.environ.get('TF_FILE_TEMPLATE','nb-template.tf.j2')
nbdev_tf_var_name           = os.environ.get('TF_VAR_NAME','nb_devices')


def main():
    session = requests.Session()
    session.verify = netbox_ssl_verify
    nb = pynetbox.api(url=netbox_url, private_key=netbox_private_key, token=netbox_token)
    nb.http_session = session
    nb_ips = nb.ipam.ip_addresses.all()
    nb_devs = nb.virtualization.virtual_machines.all()
    all_devices= {}
    device_type='VM'
    for nb_dev in nb_devs:
        device = nb_dev.serialize()
        device['device_type'] = device_type
        resource_name = re.sub('[^0-9a-zA-Z]+', '_', device['name'])
        device['tags'] = ','.join(device['tags'])
        device['custom_fields'] = json.dumps(device.get('custom_fields',{}))
        device['primary_ip_addr'] = None
        if device['primary_ip'] is not None:
            for ip in nb_ips:
                if ip.id == device['primary_ip']:
                    device['primary_ip_addr'] = str(ip).split('/')[0]
        all_devices[resource_name] = device
    nb_devs = nb.dcim.devices.all()
    device_type = 'Baremetal'
    for nb_dev in nb_devs:
        device = nb_dev.serialize()
        device['device_type'] = device_type
        resource_name = re.sub('[^0-9a-zA-Z]+', '_', device['name'])
        device['tags'] = ','.join(device['tags'])
        device['custom_fields'] = json.dumps(device.get('custom_fields',{}))
        device['primary_ip_addr'] = None
        if device['primary_ip'] is not None:
            for ip in nb_ips:
                if ip.id == device['primary_ip']:
                    device['primary_ip_addr'] = str(ip).split('/')[0]
        all_devices[resource_name] = device
    with open(tf_file_template, 'r') as read_file:
        template = Template(read_file.read())
    template.globals['regex_search'] = re.search
    print(template.render(nbdev_tf_var_name=nbdev_tf_var_name, nb_devices=all_devices))

    
    return
if __name__ == "__main__":
    main()
    