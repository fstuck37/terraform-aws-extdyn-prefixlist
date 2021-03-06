import boto3, botocore, json
import logging, traceback, os
import socket, struct
import requests
import ipaddress

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def logDictionary(dict):
	try:
		for key in dict:
			logger.info('AWS Dynamic Prefix List Lambda - Info - logDictionary - ' + str(key) + ' = ' + str(dict[key]))
	except Exception as error:
		logger.info('AWS Dynamic Prefix List Lambda - Error - logDictionary - ' + str(error))

def logList(l):
	for v in l:
		logger.info('AWS Dynamic Prefix List Lambda - Info - logList - ' + str(v) )

def getDebug():
	try:
		d = os.environ['debug']
		if d == 'True':
			return True
		else:
			return False
	except:
		return False

def getMaxEntries():
	try:
		m = os.environ['MaxEntries']
		if getDebug(): logger.info('AWS Dynamic Prefix Lambda - MaxEntries - ' + m + ' - found')
		return int(m)
	except:
		if getDebug(): logger.info('AWS Dynamic Prefix Lambda - MaxEntries - 60 - not found using default')
		return 60

def getRegion():
	try:
		r = os.environ['AWS_REGION']
		return r
	except Exception as error:
		logger.info('AWS Dynamic Prefix List Lambda - Error - getRegion - Could not retreive environment variable AWS_REGION - ' + str(error))
		return 'error'

def getPrefixConfig():
	try:
		if getDebug(): logger.info('AWS Dynamic Prefix Lambda - Debug - getPrefixConfig()')
		prefix = os.environ['prefix']
		d = dict(x.split("=") for x in prefix.split(";"))
		return d
	except Exception as error:
		logger.info('AWS Dynamic Prefix Lambda - Error - getPrefixConfig - ' + str(error))
		return None

def getURL(url):
	try:
		if getDebug(): logger.info('AWS Dynamic Prefix Lambda - Debug - getURL(' + url + ')')
		r = requests.get(url)
		data = r.text
		ips = data.splitlines()
		for ip in ips:
			try:
				i = ipaddress.ip_network(ip)
				if getDebug(): logger.info('AWS Dynamic Prefix Lambda - getURL Debug - IP = ' + ip ) 
			except ValueError as error:
				logger.info('AWS Dynamic Prefix Lambda - Error - getURL - Line does not contain an IP ' + ip)
				ips.remove(ip)
			except Exception as error:
				logger.info('AWS Dynamic Prefix Lambda - Error - getURL - Line does not contain an IP ' + ip)
				ips.remove(ip)
		return set(ips)
	except Exception as error:
		logger.info('AWS Dynamic Prefix Lambda - Error - getURL - Could not read URL = ' + url + ' error = ' + str(error))
		return None

def create_prefixlist(client, name, cidrs, maxentries):
	try:
		entries = []
		if len(cidrs) > 100:
			logger.info('AWS Dynamic Prefix Lambda - Warning - create_prefixlist - lenth of cidrs > 100 - trunkcating Prefix List ' + name)
			cidrs_limited = list(cidrs)[:100]
		else:
			cidrs_limited = list(cidrs)
		for cidr in cidrs_limited:
			entry = {'Cidr': cidr,'Description': ''}
			entries.append(entry)
		response = client.create_managed_prefix_list(DryRun=False, PrefixListName=name, Entries=entries, MaxEntries=maxentries, AddressFamily='IPv4' )
		if len(cidrs) > 100:
			update_prefixlist(client, name, cidrs)
	except Exception as error:
		logger.info('AWS Dynamic Prefix Lambda - Error - create_prefixlist - ' + str(error))
		return None

def update_prefixlist(client, name, cidrs):
	try:
		prefixlistId = get_prefixlist_id(client, name)
		prefixlistVer = get_prefixlist_ver(client, name)
		if getDebug(): logger.info('AWS Dynamic Prefix Lambda - Debug - update_prefixlist - prefixlistId = ' + str(prefixlistId) + ' & prefixlistVer = ' + str(prefixlistVer))
		paginator = client.get_paginator('get_managed_prefix_list_entries')
		response = paginator.paginate(DryRun=False, PrefixListId=prefixlistId)
		entries = []
		for l in response:
			entries.extend(l['Entries'])
		if getDebug(): logger.info('AWS Dynamic Prefix Lambda - Debug - update_prefixlist - response entries')
		if getDebug(): logList(entries)
		if getDebug(): logger.info('AWS Dynamic Prefix Lambda - Debug - update_prefixlist -  build existing')
		existing = []
		if len(entries) > 0:
			for c in entries:
				existing.append(c['Cidr'])
		else:
			logger.info('AWS Dynamic Prefix Lambda - Error - update_prefixlist - response[Entries] = 0 - ' + name)
		if getDebug(): logger.info('AWS Dynamic Prefix Lambda - Debug - update_prefixlist -  existing ' + str(existing))
		cidr_add = compare(set(cidrs), set(existing))
		cidr_remove = compare(set(existing), set(cidrs))
		# Build entries_add
		if getDebug(): logger.info('AWS Dynamic Prefix Lambda - Debug - update_prefixlist -  build entries_add')
		entries_add = []
		if len(cidr_add) > 100:
			logger.info('AWS Dynamic Prefix Lambda - Warning - update_prefixlist - lenth of cidr_add > 100 - trunkcating Prefix List ' + name)
			cidrs_add_limited = list(cidr_add)[:100]
		else:
			cidrs_add_limited = list(cidr_add)
		for cidr in cidrs_add_limited:
			entry = {'Cidr': cidr,'Description': ''}
			entries_add.append(entry)
		if getDebug(): logger.info('AWS Dynamic Prefix Lambda - Debug - update_prefixlist - entries_add ' + str(entries_add))
		# Build entries_remove
		if getDebug(): logger.info('AWS Dynamic Prefix Lambda - Debug - update_prefixlist -  build entries_remove')
		entries_remove = []
		if len(cidr_remove) > 100:
			logger.info('AWS Dynamic Prefix Lambda - Warning - update_prefixlist - lenth of cidr_remove > 100 - trunkcating Prefix List ' + name)
			cidrs_remove_limited = list(cidr_remove)[:100]
		else:
			cidrs_remove_limited = list(cidr_remove)
		for cidr in cidrs_remove_limited:
			entry = {'Cidr': cidr}
			entries_remove.append(entry)
		if getDebug(): logger.info('AWS Dynamic Prefix Lambda - Debug - update_prefixlist - entries_remove ' + str(entries_remove))
		if len(entries_add)>0 or len(entries_remove)>0:
			mod_response = client.modify_managed_prefix_list(DryRun=False, PrefixListId=prefixlistId, AddEntries=entries_add, RemoveEntries=entries_remove, CurrentVersion=prefixlistVer)
		else:
			if getDebug(): logger.info('AWS Dynamic Prefix Lambda - Debug - update_prefixlist - no changes required')
	except Exception as error:
		logger.info('AWS Dynamic Prefix Lambda - Error - update_prefixlist - ' + str(error))
		return None

def get_prefixlist_id(client, name):
	try:
		if getDebug(): logger.info('AWS Dynamic Prefix Lambda - Debug - get_prefixlist_id -  prefixlist = ' + name )
		filters = [{'Name': 'prefix-list-name', 'Values': [name]}]
		response = client.describe_managed_prefix_lists(Filters=filters)
		prefixlist = response['PrefixLists']
		if getDebug(): logger.info('AWS Dynamic Prefix Lambda - Debug - get_prefixlist_id -  prefixlist ' + str(prefixlist))
		if len(prefixlist)==1:
			return prefixlist[0]['PrefixListId']
		elif len(prefixlist)>1:
			logger.info('AWS Dynamic Prefix Lambda - Warning - prefixlist_exists -  prefixlist_exists(' + name + ') retuned ' + len(prefixlist) + ' which is more than 1')
			return prefixlist[0]['PrefixListId']
		else:
			return None
	except Exception as error:
		logger.info('AWS Dynamic Prefix Lambda - get_prefixlist_id - Error - ' + str(error))
		return None

def get_prefixlist_ver(client, name):
	try:
		if getDebug(): logger.info('AWS Dynamic Prefix Lambda - Debug - get_prefixlist_ver -  prefixlist = ' + name )
		filters = [{'Name': 'prefix-list-name', 'Values': [name]}]
		response = client.describe_managed_prefix_lists(Filters=filters)
		if getDebug(): logger.info('AWS Dynamic Prefix Lambda - Debug - get_prefixlist_ver - ' + str(response))
		prefixlist = response['PrefixLists']
		if len(prefixlist)==1:
			return prefixlist[0]['Version']
		elif len(prefixlist)>1:
			return prefixlist[0]['Version']
		else:
			return None
	except Exception as error:
		logger.info('AWS Dynamic Prefix Lambda - get_prefixlist_ver - Error - ' + str(error))
		return None

def prefixlist_exists(client, name):
	try:
		if getDebug(): logger.info('AWS Dynamic Prefix Lambda - Debug - prefixlist_exists -  prefixlist (' + name + ')')
		filters = [{'Name': 'prefix-list-name', 'Values': [name]}]
		response = client.describe_managed_prefix_lists(Filters=filters)
		prefixlist = response['PrefixLists']
		if getDebug(): logger.info('AWS Dynamic Prefix Lambda - Debug - prefixlist_exists -  prefixlist ' + str(prefixlist))
		if len(prefixlist)==1:
			return True
		elif len(prefixlist)>1:
			logger.info('AWS Dynamic Prefix Lambda - Warning - prefixlist_exists -  prefixlist_exists(' + name + ') retuned ' + len(prefixlist) + ' which is more than 1')
			return True
		else:
			return False
	except Exception as error:
		logger.info('AWS Dynamic Prefix Lambda - prefixlist_exists Error - error - ' + str(error))
		return False
		
def compare(xset, yset):
	yset = set(yset)
	return [item for item in xset if item not in yset]

def lambda_handler(event, context):
	if getDebug(): logger.info('AWS Dynamic Prefix Lambda - Debug - Started with Debugging enabled')
	if getDebug(): logger.info('AWS Dynamic Prefix Lambda - Debug - Triggering Event: ' + str(event))
	try:
		if getDebug(): logger.info('AWS Dynamic Prefix Lambda - Debug - Get information')
		region      = getRegion()
		session     = boto3.Session(region_name=region)
		ec2         = session.client('ec2')
		prefixlists = getPrefixConfig()
		if getDebug(): logger.info('AWS Dynamic Prefix Lambda - Debug - information - region=' + str(region))
		if getDebug(): logDictionary(prefixlists)
		for prefixlist_key in prefixlists:
			prefixlist_value = prefixlists[prefixlist_key]
			prefixlist_cidrs = getURL(prefixlist_value)
			maxentries = getMaxEntries()
			if getDebug(): logger.info('AWS Dynamic Prefix Lambda - Debug - prefixlist_key: ' + str(prefixlist_key))
			if getDebug(): logList(prefixlist_cidrs)
			if prefixlist_exists(ec2, prefixlist_key):
				if getDebug(): logger.info('AWS Dynamic Prefix Lambda - Debug - prefix list exists update')
				update_prefixlist(ec2, prefixlist_key, prefixlist_cidrs)
			else:
				if getDebug(): logger.info('AWS Dynamic Prefix Lambda - Debug - prefix list does not exist create it')
				create_prefixlist(ec2, prefixlist_key, prefixlist_cidrs, maxentries)
	except Exception as error:
		logger.info('AWS Dynamic Prefix Lambda - Error ' + traceback.format_exc())
		logger.info('AWS Dynamic Prefix Lambda - lambda_handler - Error - ' + str(error))