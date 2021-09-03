from botocore.vendored import requests
import boto3, botocore, json
import logging, traceback, os
import socket, struct
import requests
import ipaddress

logger = logging.getLogger()
logger.setLevel(logging.INFO)

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
		logger.info('AWSviaNATGW Lambda - Error - Could not retreive environment variable AWS_REGION')
		return 'error'

def getPrefixConfig():
	try:
		if getDebug(): logger.info('AWS Dynamic Prefix Lambda - Debug - getPrefixConfig()')
		d = os.environ.items()
		try:
			del d['AWS_REGION']
		except:
			pass
		try:
			del d['debug']
		except:
			pass
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
		for prefixlist_key in prefixlists:
			prefixlist_value = prefixlists[prefixlist_key]
			prefixlist_cidrs = getURL(prefixlist_value)
			if getDebug(): logger.info('AWS Dynamic Prefix Lambda - Debug - prefixlist_key: ' + prefixlist_key)
			if getDebug(): logger.info('AWS Dynamic Prefix Lambda - Debug - prefixlist_value: ' + prefixlist_value)
			if getDebug(): logger.info('AWS Dynamic Prefix Lambda - Debug - prefixlist_cidrs: ' + prefixlist_cidrs)
			prefixlist_exists(ec2, prefixlist_key)
	except:
		logger.info('AWS Dynamic Prefix Lambda - Error ' + traceback.format_exc())

		new_routes = getAWSips(services, regions)
		filters    = [{'Name': 'vpc-id', 'Values': AWSvpcids}]
		routes     = ec2.describe_route_tables(Filters=filters)
		logger.info('AWS Dynamic Prefix Lambda - Info [region, account, AWSvpcids, New Routes, Route Limit]: ' + str(region) + ' ' + str(account) + ' ' + str(AWSvpcids) + ' ' + str(new_routes) + ' ' + str(limit))
		
		if getDebug(): logger.info('AWS Dynamic Prefix Lambda - Debug - Start Loop')
		for i in range(0, len(routes['RouteTables'])):
			routes_dict = routes['RouteTables'][i]['Routes']
			if getDebug(): logger.info('AWS Dynamic Prefix Lambda - Debug - routes dictionary: ' + str(routes_dict))
			route_table_id = routes['RouteTables'][i]['RouteTableId']
			if getDebug(): logger.info('AWS Dynamic Prefix Lambda - Debug - route table ID: ' + str(route_table_id))
			existing_cidrs = []
			nat_gw_id = ''
			for y in range(0, len(routes_dict)):
				if getDebug(): logger.info('AWS Dynamic Prefix Lambda - Debug - routes_dict[' + str(y) + ']: ' + str(routes_dict[y]))
				if 'DestinationPrefixListId' not in routes_dict[y]:
					if routes_dict[y]['Origin'] == "CreateRoute":
						if 'NatGatewayId' in routes_dict[y]:
							nat_gw_id = routes_dict[y]['NatGatewayId']
							if getDebug(): logger.info('AWS Dynamic Prefix Lambda - Debug - NAT Gateway ID: ' + str(nat_gw_id))
							route = routes_dict[y]['DestinationCidrBlock']
							existing_cidrs.append(route)
							if route not in new_routes and route not in ignore:
								if getDebug(): logger.info('AWS Dynamic Prefix Lambda - Debug - routes_dict[' + str(y) + '][DestinationCidrBlock]: ' + str(routes_dict[y]['DestinationCidrBlock']))
								try:
									ec2.delete_route(
										DestinationCidrBlock=route,
										DryRun=False,
										RouteTableId=route_table_id
									)
									logger.info('AWS Dynamic Prefix Lambda - Info Deleted Route ' + str(route) + ' in rotuing table ' + str(route_table_id))
								except:
									logger.info('AWS Dynamic Prefix Lambda - Error Deleting Route ' + str(route) + ' in rotuing table ' + str(route_table_id))
									logger.info('AWS Dynamic Prefix Lambda - Error Deleting Route Detail ' + traceback.format_exc())
			
			new_routes_final = compare(new_routes, existing_cidrs)
			if getDebug(): logger.info('AWS Dynamic Prefix Lambda - Debug - Existing Routes: ' + str(existing_cidrs))
			if getDebug(): logger.info('AWS Dynamic Prefix Lambda - Debug - New Routes to add: ' + str(new_routes_final))

			if nat_gw_id != "":
				for route in new_routes_final:
					try:
						ec2.create_route(
							DestinationCidrBlock=route,
							DryRun=False,
							NatGatewayId=nat_gw_id,
							RouteTableId=route_table_id,
						)
						logger.info('AWS Dynamic Prefix Lambda - Info Added Route ' + str(route) + ' in rotuing table ' + str(route_table_id))
					except:
						logger.info('AWS Dynamic Prefix Lambda - Error Adding Route ' + str(route) + ' in rotuing table ' + str(route_table_id))
						logger.info('AWS Dynamic Prefix Lambda - Error Adding Route Detail ' + traceback.format_exc())
			else:
				if getDebug(): logger.info('AWS Dynamic Prefix Lambda - Debug - No NAT Gateway found for route table ' + str(route_table_id))
		if getDebug(): logger.info('AWS Dynamic Prefix Lambda - Debug - End Loop')
