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

def create_prefixlist(client, name, cidrs):
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
		response = client.create_managed_prefix_list(DryRun=False, PrefixListName=name, Entries=entries, MaxEntries=1000,AddressFamily='IPv4' )
	except Exception as error:
		logger.info('AWS Dynamic Prefix Lambda - Error - create_prefixlist - ' + str(error))
		return None

def update_prefixlist(client, name, cidrs):
	try:
		prefixlistId = get_prefixlist_id(client, name)
		response = client.get_managed_prefix_list_entries(DryRun=False, PrefixListId=prefixlistId )
		if getDebug(): logger.info('AWS Dynamic Prefix Lambda - Debug - update_prefixlist - response ' + str(response))
		if getDebug(): logger.info('AWS Dynamic Prefix Lambda - Debug - update_prefixlist -  build existing')
		existing = []
		if len(response['Entries']) > 0:
			for c in response['Entries']:
				existing.append(c['Cidr'])
		else:
			logger.info('AWS Dynamic Prefix Lambda - Error - update_prefixlist - response[Entries] = 0 - ' + name)
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
		if getDebug(): logger.info('AWS Dynamic Prefix Lambda - Debug - update_prefixlist -  build entries_remove')
		# Build entries_remove
		entries_remove = []
		if len(cidr_remove) > 100:
			logger.info('AWS Dynamic Prefix Lambda - Warning - update_prefixlist - lenth of cidr_remove > 100 - trunkcating Prefix List ' + name)
			cidrs_remove_limited = list(cidr_remove)[:100]
		else:
			cidrs_add_limited = list(cidr_remove)
		for cidr in cidrs_remove_limited:
			entry = {'Cidr': cidr}
			entries_remove.append(entry)
		if getDebug(): logger.info('AWS Dynamic Prefix Lambda - Debug - update_prefixlist - entries_remove ' + str(entries_remove))
		mod_response = client.modify_managed_prefix_list(DryRun=False, PrefixListId=prefixlistId, AddEntries=entries_add, RemoveEntries=entries_remove )
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
		test_cidrs1 = ['10.0.0.0/16', '192.168.0.0/16', '172.16.0.0/12', '192.168.0.0/24']
		test_cidrs2 = ['10.0.0.0/16', '192.168.0.0/16', '172.16.0.0/12']
		test_add = compare(test_cidrs1, test_cidrs2)
		test_remove = compare(test_cidrs2, test_cidrs1)
		logger.info('AWS Dynamic Prefix Lambda - Debug - test_add: ' + str(test_add))
		logger.info('AWS Dynamic Prefix Lambda - Debug - test_remove: ' + str(test_remove))
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
			if getDebug(): logger.info('AWS Dynamic Prefix Lambda - Debug - prefixlist_key: ' + str(prefixlist_key))
			if getDebug(): logList(prefixlist_cidrs)
			if prefixlist_exists(ec2, prefixlist_key):
				if getDebug(): logger.info('AWS Dynamic Prefix Lambda - Debug - prefix list exists update')
				update_prefixlist(ec2, prefixlist_key, prefixlist_cidrs)
				if getDebug(): logger.info('AWS Dynamic Prefix Lambda - TEST - update with test_cidrs2')
				update_prefixlist(ec2, prefixlist_key, test_cidrs2)
				if getDebug(): logger.info('AWS Dynamic Prefix Lambda - TEST - update with test_cidrs1')
				update_prefixlist(ec2, prefixlist_key, test_cidrs1)
			else:
				if getDebug(): logger.info('AWS Dynamic Prefix Lambda - Debug - prefix list does not exist create it')
				create_prefixlist(ec2, prefixlist_key, prefixlist_cidrs)
	except Exception as error:
		logger.info('AWS Dynamic Prefix Lambda - Error ' + traceback.format_exc())
		logger.info('AWS Dynamic Prefix Lambda - lambda_handler - Error - ' + str(error))