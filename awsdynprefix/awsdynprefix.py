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
	except:
		logger.info('AWS Dynamic Prefix List Lambda - Error - logDictionary - ')

def logList(l):
	for v in l:
		logger.info('AWS Dynamic Prefix List Lambda - Info - logList - ' + str(l) )

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
	except:
		logger.info('AWS Dynamic Prefix List Lambda - Error - Could not retreive environment variable AWS_REGION')
		return 'error'

def getPrefixConfig():
	try:
		if getDebug(): logger.info('AWS Dynamic Prefix Lambda - Debug - getPrefixConfig()')
		prefix = os.environ['prefix']
		d = dict(x.split("=") for x in prefix.split(";"))
		return d
	except:
		return None

def getURL(url):
	try:
		if getDebug(): logger.info('AWS Dynamic Prefix Lambda - getURL Debug - getURL(' + url + ')')
		r = requests.get(url)
		data = r.text
		ips = data.splitlines()
		for ip in ips:
			try:
				i = ipaddress.ip_network(ip)
				if getDebug(): logger.info('AWS Dynamic Prefix Lambda - getURL Debug - IP = ' + ip ) 
			except ValueError as error:
				logger.info('AWS Dynamic Prefix Lambda - getURL Error - Line does not contain an IP ' + ip)
				ips.remove(ip)
			except Exception as error:
				logger.info('AWS Dynamic Prefix Lambda - getURL Error - Line does not contain an IP ' + ip)
				ips.remove(ip)
		return set(ips)
	except:
		print(inst)
		logger.info('AWS Dynamic Prefix Lambda - getURL Error - Could not read URL = ' + url + ' error = ' + error)
		return None


def prefixlist_exists(client, name):
	try:
		response = client.describe_managed_prefix_lists(
			DryRun=True|False,
			Filters=[
				{
					'Name': 'string',
					'Values': [name]
				}
			],
			MaxResults=123
		)
		logger.info('AWS Dynamic Prefix Lambda - prefixlist_exists TEST - ' + response['PrefixLists'][0])
		# need to check if response is valid and return true or false -----------------------------------------------------------
	except:
		logger.info('AWS Dynamic Prefix Lambda - prefixlist_exists Error - error')

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
		if getDebug(): logDictionary(prefixlists)
		for prefixlist_key in prefixlists:
			prefixlist_value = prefixlists[prefixlist_key]
			prefixlist_cidrs = getURL(prefixlist_value)
			if getDebug(): logDictionary(prefixlist_cidrs)
			# if getDebug(): logger.info('AWS Dynamic Prefix Lambda - Debug - prefixlist_key: ' + ''.join(map(str,prefixlist_key)))
			# if getDebug(): logger.info('AWS Dynamic Prefix Lambda - Debug - prefixlist_key: ' + prefixlists[prefixlist_key])
			# if getDebug(): logger.info('AWS Dynamic Prefix Lambda - Debug - prefixlist_value: ' + prefixlist_value)
			# if getDebug(): logger.info('AWS Dynamic Prefix Lambda - Debug - prefixlist_cidrs: ' + prefixlist_cidrs)
			# prefixlist_exists(ec2, prefixlist_key)
	except Exception as e:
		logger.info('AWS Dynamic Prefix Lambda - Error ' + traceback.format_exc())
		logger.info(e)