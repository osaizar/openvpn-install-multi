#!/usr/bin/python3

import os
import sys
import re
import subprocess

OPENVPN_BASE_CONFIG_DIR = "/etc/openvpn/"
INSTANCES_FILE = OPENVPN_BASE_CONFIG_DIR+"instances"

def create_instances_file():
	os.makedirs(OPENVPN_BASE_CONFIG_DIR, exist_ok=True)
	with open(INSTANCES_FILE, "w") as instance_file:
		instance_file.write("# Created by openvpn_multiple_instances.py, DO NOT EDIT!\n")
		instance_file.write("# Instance Name;Port;Protocol;Network\n")


def read_instances():
	instances = []
	if not os.path.isfile(INSTANCES_FILE):
		return instances

	with open(INSTANCES_FILE, "r") as instance_file:
		for l in instance_file.read().split("\n"):
			if not re.match(r"^\s*#(.*)", l) and not l == "": # Check if comment
				l = l.split(";")
				l = [e.strip() for e in l]
				instances.append({"name" : l[0], "port" : l[1], "protocol" : l[2], "network" : l[3]})
	
	return instances


def append_instance(instance):
	with open(INSTANCES_FILE, "a") as instance_file:
		instance_file.write("{};{};{};{}\n".format(instance["name"], instance["port"], instance["protocol"], instance["network"]))


def configure_new_instance(instances):
	if instances:
		print("These are the current instances: ")
		print("Instance Name\tPort\tNetwork")
		for i in instances:
			print("{}\t{}/{}\t{}".format(i["name"], i["port"], i["protocol"], i["network"]))
		print("Do not overlap configurations!")
	
	valid_instance = False

	while not valid_instance:
		name = input("Enter a instance name to use: ")

		protocol = False
		while not protocol:
			print("Which protocol should OpenVPN use?")
			print("\t1) UDP (recomended)")
			print("\t2) TCP")

			try:
				protocol = int(input("Protocol [1]: ") or "1")
			except:
				protocol = False

			if protocol in [1,2]:
				if protocol == 1:
					protocol = "udp"
				else:
					protocol = "tcp"
			else:
				print("Invalid value!")
				protocol = False

		port = False
		while not port:
			print("Which port should OpenVPN use?")

			try:
				port = int(input("Port [1194]: ") or "1194")
			except:
				port = False

			if port < 65535:
				port = str(port)
			else:
				print("{} is not a valid port".format(port))
				port = False
		
		network = False
		while not network:
			print("Which internal network should OpenVPN use?")
		
			try:
				network = input("Enter a network, /24 netmask will be used: ")
			except:
				network = False
			
			network = network.strip()

			if not re.match(r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$", network):
				print("{} is not a valid IPv4 address".format(network))
				network = False
			elif not re.match(r"^(?:10|127|172\.(?:1[6-9]|2[0-9]|3[01])|192\.168)\..*", network):
				print("{} is not a private IPv4 /24 network address".format(network))
				network = False

		unique = True
		new_instance = {"name" : name, "port" : port, "protocol" : protocol, "network" : network}
		for i in instances:
			if new_instance["name"] == i["name"] or new_instance["network"] == i["network"] or (new_instance["port"] == i["port"] and new_instance["protocol"] == i["protocol"]):
				print("{}\nis not a valid configuration, overlaps with: \n{}".format(new_instance, i))
				unique = False
		
		if unique:
			valid_instance = True
	
	return new_instance


def create_instance(instance):
	append_instance(instance)
	subprocess.run(["/bin/bash", "openvpn-install-multiple.sh", instance["name"], instance["port"], instance["protocol"], instance["network"]])



if __name__ == '__main__':
	if not os.geteuid() == 0:
		print("Run this script as root!")
		sys.exit()

	instances = read_instances()

	if not instances: # new install
		create_instances_file()
		new_instance = configure_new_instance(instances)
		create_instance(new_instance)
	else: # manage a install
		pass