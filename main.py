#!/usr/bin/env python

# from novaclient.v2 import client
import logging
from os import environ as env
from datetime import datetime
import sys

import matplotlib.pyplot as plt

logging.basicConfig(level=logging.INFO)

keystone = dict(os_username=env['OS_USERNAME'],
                os_password=env['OS_PASSWORD'],
                os_auth_url=env['OS_AUTH_URL'],
                os_tenant_name=env['OS_TENANT_NAME'])
client = None


def get_available_resource_ids(cc, metric):
    """
    Get all instances Id in Ceilometer
    """
    inst_list = list()
    meters_list = cc.meters.list()
    [inst_list.append(meters.resource_id) for meters in meters_list if meters.name == metric]
    return inst_list


def search_samples(cc, inst_list, instance_uuid):
    for instance in inst_list:
        if instance == instance_uuid:
            query = [dict(field='resource', op='eq', value=instance)]
            samples = cc.samples.list(meter_name=meters[0], q=query)
            samples = list(reversed(samples))
            return samples
    return []


def generate_figure(cc, instance_uuid, samples, metric_label, output_file):
    """
    Get csv file containing data provided as a parameter
    """
    min_date = None
    x = []
    y = []
    if samples:
        for sample in samples:
            try:
                sample_date = datetime.strptime(sample.recorded_at, '%Y-%m-%dT%H:%M:%S.%f')
            except ValueError:
                sample_date = datetime.strptime(sample.recorded_at, '%Y-%m-%dT%H:%M:%S')
            time_since_epoch = (sample_date-datetime(1970, 1, 1)).total_seconds()
            if min_date is None or time_since_epoch < min_date:
                min_date = time_since_epoch
            value = sample.counter_volume
            x += [time_since_epoch]
            y += [value]

    x = map(lambda v: v - min_date, x)

    # plot
    plt.plot(x,y)
    # beautify the x-labelso
    plt.gcf().autofmt_xdate()

    plt.xlabel('time since beginning of experiment (s)')
    plt.ylabel(metric_label)
    plt.title("%s over time" % (metric_label.capitalize()))

    plt.savefig(output_file)


def print_help():
    print("Please run the program with the following pattern:")
    print("%s <instance_uuid> [<metric> <output_file>]" % (sys.argv[0]))

if __name__ == "__main__":

    if len(sys.argv) < 2:
        print_help()
        sys.exit(1)

    instance_uuid = sys.argv[1]

    if len(sys.argv) < 3:
        targeted_metric_name = "hardware.cpu.load.1min"
    else:
        targeted_metric_name = sys.argv[2]

    if len(sys.argv) < 4:
        output_file = "output.png"
    else:
        output_file = sys.argv[3]

    required_env_vars = ['OS_AUTH_URL', 'OS_TENANT_NAME', 'OS_USERNAME', 'OS_PASSWORD', 'OS_REGION_NAME']

    from ceilometerclient import client

    client = client.get_client(2, **keystone)

    meters = [targeted_metric_name]
    # instance_list = get_available_resource_ids(client, targeted_metric_name)
    samples = search_samples(client, [instance_uuid], instance_uuid)
    generate_figure(client, instance_uuid, samples, targeted_metric_name, output_file)
