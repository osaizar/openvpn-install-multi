#!/usr/bin/python3

import os
import sys
import re
import subprocess

OPENVPN_BASE_CONFIG_DIR = "/etc/openvpn/"
INSTANCES_FILE = OPENVPN_BASE_CONFIG_DIR+"instances"

DEFAULT_NAME = "inst0"
DEFAULT_PORT = "1194"
DEFAULT_NETWORK = "10.0.0.0"

def get_default_free_port(instances):
	port = DEFAULT_PORT
	end = False
	while not end:
		found = False
		for i in instances:
			if i["port"] == port:
				found = True
		if found:
			port = str(int(port) + 1)
		else:
			end = True
	
	return str(port)


def get_default_free_network(instances):
	network = DEFAULT_NETWORK
	end = False
	while not end:
		found = False
		for i in instances:
			if i["network"] == network:
				found = True
		if found:
			nets = network.split(".")
			if nets[2] != "254":
				nets[2] = str(int(nets[2]) + 1)
			else:
				nets[1] = str(int(nets[1]) + 1)
				nets[2] = "0"

			network = ".".join(nets)
		else:
			end = True
	
	return network


def get_default_free_name(instances):
	name = DEFAULT_NAME
	end = False
	while not end:
		found = False
		for i in instances:
			if i["name"] == name:
				found = True
		if found:
			id = str(int(name[-1]) + 1)
			name = list(name)
			name[-1] = id
			name = "".join(name)
		else:
			end = True
	
	return name



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
				instances.append({"name" : l[0], "port" : l[1], "protocol" : l[2], "network" : l[3], "service" : "openvpn-server-multi@server-{}.service".format(l[0])})
	
	return instances


def append_instance(instance):
	with open(INSTANCES_FILE, "a") as instance_file:
		instance_file.write("{};{};{};{}\n".format(instance["name"], instance["port"], instance["protocol"], instance["network"]))


def print_instances(instances):
	print("#)\tName\tPort\t\tNetwork\t\tService")
	for i, ins in enumerate(instances):
		print("{})\t{}\t{}/{}\t{}\t{}".format(i+1, ins["name"], ins["port"], ins["protocol"], ins["network"], ins["service"]))


def configure_new_instance(instances):
	if instances:
		print("These are the current instances: ")
		print_instances(instances)
		print("Do not overlap configurations!")
	
	valid_instance = False

	while not valid_instance:
		default_name = get_default_free_name(instances)
		name = input("Enter a instance name to use [{}]: ".format(default_name))
		if not name:
			name = default_name

		protocol = False
		while not protocol:
			print("Which protocol should OpenVPN use?")
			print("\t1) UDP (recomended)")
			print("\t2) TCP")

			try:
				protocol = int(input("Protocol [1]: ") or "1")
			except KeyboardInterrupt:
				sys.exit()
			except:
				print("Invalid value!")
				protocol = False
				continue

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
			default_port = get_default_free_port(instances)

			try:
				port = int(input("Port [{}]: ".format(default_port)) or default_port)
			except KeyboardInterrupt:
				sys.exit()
			except:
				print("Invalid value!")
				port = False
				continue

			if port < 65535:
				port = str(port)
			else:
				print("{} is not a valid port".format(port))
				port = False
		
		network = False
		while not network:
			print("Which internal network should OpenVPN use?")
			default_network = get_default_free_network(instances)
		
			try:
				network = input("Enter a network, /24 netmask will be used [{}]: ".format(default_network))
			except KeyboardInterrupt:
				sys.exit()
			except:
				print("Invalid value!")
				network = False
				continue
			
			network = network.strip()

			if not network:
				network = default_network

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
	subprocess.run(["/bin/bash", ".openvpn-install-multi.sh", instance["name"], instance["port"], instance["protocol"], instance["network"]])


def manage_instances(instances):
	ans = False
	while not ans:
		ans = input("Instance id? ")
		try:
			ans = int(ans)
			selected_instance = instances[ans-1]
		except KeyboardInterrupt:
			sys.exit()
		except:
			print("Invalid value!")
			ans = False
			continue
	
	subprocess.run(["/bin/bash", ".openvpn-install-multi.sh", selected_instance["name"], selected_instance["port"], selected_instance["protocol"], selected_instance["network"]])


if __name__ == '__main__':
	if not os.geteuid() == 0:
		print("Run this script as root!")
		sys.exit()

	instances = read_instances()

	if not instances: # new instance
		create_instances_file()
		new_instance = configure_new_instance(instances)
		create_instance(new_instance)
	else:
		print("Current instances:")
		print_instances(instances)
		ans = False
		while not ans:
			print("What do you need to do?")
			print("1) Manage a instance\n2) Create a new instance")
			
			try:
				ans = input("> ")
			except KeyboardInterrupt:
				sys.exit()

			if ans == "1":
				manage_instances(instances)
			elif ans == "2":
				new_instance = configure_new_instance(instances)
				create_instance(new_instance)
			else:
				print("{} is not a valid answer!".format(ans))
				ans = False
