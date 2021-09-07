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
		logger.info('AWS Dynamic Prefix List Lambda - Error - logDictionary - ' + error)

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
		logger.info('AWS Dynamic Prefix List Lambda - Error - getRegion - Could not retreive environment variable AWS_REGION - ' + error )
		return 'error'

def getPrefixConfig():
	try:
		if getDebug(): logger.info('AWS Dynamic Prefix Lambda - Debug - getPrefixConfig()')
		prefix = os.environ['prefix']
		d = dict(x.split("=") for x in prefix.split(";"))
		return d
	except Exception as error:
		logger.info('AWS Dynamic Prefix Lambda - Error - getPrefixConfig - ' + error)
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
		logger.info('AWS Dynamic Prefix Lambda - Error - getURL - Could not read URL = ' + url + ' error = ' + error)
		return None

def create_prefixlist(client, name, cidrs):
	try:
		entries = [{'Cidr': '10.0.0.0/16','Description': 'Test1'},]
		response = client.create_managed_prefix_list(DryRun=False, PrefixListName=name, Entries=entries, MaxEntries=123,AddressFamily='IPv4' )
	except Exception as error:
		logger.info('AWS Dynamic Prefix Lambda - Error - create_prefixlist - ' + error)
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
		logger.info('AWS Dynamic Prefix Lambda - prefixlist_exists Error - error - ' + error)
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
			if getDebug(): logger.info('AWS Dynamic Prefix Lambda - Debug - prefixlist_key: ' + str(prefixlist_key))
			if getDebug(): logList(prefixlist_cidrs)
			if prefixlist_exists(ec2, prefixlist_key):
				if getDebug(): logger.info('AWS Dynamic Prefix Lambda - Debug - prefix list exists update')
			else:
				if getDebug(): logger.info('AWS Dynamic Prefix Lambda - Debug - prefix list does not exist create it')
				create_prefixlist(ec2, prefixlist_key, prefixlist_cidrs)
	except Exception as e:
		logger.info('AWS Dynamic Prefix Lambda - Error ' + traceback.format_exc())
		logger.info(e)
