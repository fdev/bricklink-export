#!/usr/bin/env python

from __future__ import print_function

import itertools
import argparse
import json
import sys
import re
import os
from getpass import getpass
from ConfigParser import SafeConfigParser


def main():
	# Import non-standard modules
	try:
		import requests
	except ImportError:
		sys.exit("Python module 'requests' not found.\nPlease install using: pip install requests")

	try:
		from pyquery import PyQuery as pq
	except ImportError:
		sys.exit("Python module 'pyquery' not found.\nPlease install using: pip install pyquery")

	# Support both 2.x and 3.x
	try:
		input = raw_input
	except NameError:
		pass
	
	# Helper functions
	def strip(s):
		return re.sub(r'[\s\xa0]+', ' ', s).strip() # \xa0 is &nbsp;

	def encode(html):
		return unicode(html).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&#39;')
	
	def verbose(s):
		if args.verbose:
			print(s, file=sys.stderr)
	
	# Command arguments
	parser = argparse.ArgumentParser(description='Export a BrickLink wanted list.')
	parser.add_argument('--version', action='version', version='bricklink-export 1.1')
	parser.add_argument('-v', '--verbose', dest='verbose', action='store_true', default=False, help='be verbose')
	parser.add_argument('-u', '--username', dest='username', help='username on BrickLink')
	parser.add_argument('-p', '--password', dest='password', help='password on BrickLink (omit for prompt)')
	parser.add_argument('-l', '--list', dest='list', action='store_true', default=False, help='list of wanted lists')
	parser.add_argument('-c', '--colors', dest='colors', action='store_true', default=False, help='list of colors')
	parser.add_argument('-e', '--export', dest='export', metavar='ID', type=int, help='wanted list to export')
	parser.add_argument('-w', '--wanted', dest='wanted', metavar='ID', type=int, help='override wanted list id in export')
	args = parser.parse_args()
	
	# Requests session
	session = requests.Session()
	session.headers.update({'User-Agent': 'bricklink-export 1.1 (http://github.com/fdev/bricklink-export)'})
	
	# List and export require authentication
	if args.list or args.export is not None:
		username = args.username
		password = args.password
		
		# Credentials file
		config = SafeConfigParser()
		config.read([os.path.expanduser('~/.bricklink-export.conf'), os.path.expanduser('~/bricklink-export.ini')])

		# Look for username in config file if not given
		if not username:
			try:
				username = config.get('user', 'username')
				verbose('Read username from config file: %s' % username)
			except:
				pass
			
		# Request username if not given
		if not username:
			verbose('No username specified.')
			try:
				username = input('Enter username: ')
			except KeyboardInterrupt:
				sys.exit(1)

		# Look for password in config file if not given
		if not password:
			try:
				password = config.get('user', 'password')
				verbose('Read password from config file.')
			except:
				pass
			
		# Request password if not given
		if not password:
			verbose('No password specified.')
			try:
				password = getpass('Enter password: ')
			except KeyboardInterrupt:
				sys.exit(1)

		# Authenticate
		verbose('Authenticating.')
		payload = {
			'pageId': 'LOGIN',
			'userid': username,
			'password': password,
		}
		r = session.post('https://www.bricklink.com/ajax/renovate/login.ajax', data=payload, allow_redirects=False)

		if not r:
			sys.exit('Could not log in to BrickLink.')

		try:
			data = json.loads(r.text)
		except:
			sys.exit('Invalid JSON in authentication response.')


		if data.get('returnCode') != 0:
			sys.exit('Invalid username or password specified.')

		verbose('Authenticated as %s.' % username)

	# Color list
	if args.colors:
		verbose('Retrieving color guide.')
		r = session.get('https://www.bricklink.com/catalogColors.asp')
		if not r:
			sys.exit('Could not retrieve color guide.')

		verbose('Parsing.')
		html = pq(r.text)
		tables = html('table tr')

		colors = []
		for table in map(pq, tables):
			if len(table('td')) == 9 and strip(table('td:nth-child(9)').text()) != 'Color Timeline':
				id = strip(table('td:nth-child(1)').text())
				name = strip(table('td:nth-child(4)').text())

				if not id.isdigit() or not name:
					sys.exit('Unexpected color guide format.')

				colors.append({
					'id': id,
					'name': name,
				})

		print('ID\tName')
		for color in colors:
			print('%s\t%s' % (color['id'], color['name']))
		sys.exit()
	
	# List of wanted lists
	if args.list:
		verbose('Retrieving list of wanted lists.')
		r = session.get('https://www.bricklink.com/v2/wanted/list.page')
		if not r:
			sys.exit('Could not retrieve wanted lists.')

		verbose('Parsing.')

		match = re.search(r'var wlJson = (\{.+?\});\r?\n', r.text, re.MULTILINE)
		if not match:
			sys.exit('Unexpected wanted list page format.')

		try:
			data = json.loads(match.group(1))
		except:
			sys.exit('Invalid JSON found in wanted list page.')

		# Assert expected data
		if not isinstance(data, dict) or not isinstance(data.get('wantedLists'), list):
			sys.exit('Unexpected JSON content in wanted list page.')

		# Print list
		print('ID\tItems\tName')
		for row in data['wantedLists']:
			print('%s\t%s\t%s' % (row['id'], row['num'], row['name']))
	
		sys.exit()

	# Export
	if args.export is not None:
		items = []

		for page in itertools.count(1):
			verbose('Retrieving page %d...' % page)

			r = session.get('https://www.bricklink.com/v2/wanted/search.page?type=A&wantedMoreID=%d&sort=1&pageSize=100&page=%d' % (args.export, page))
			if not r:
				sys.exit('Could not retrieve page %d of part list.' % page)

			verbose('Parsing.')

			match = re.search(r'var wlJson = (\{.+?\});\r?\n', r.text, re.MULTILINE)
			if not match:
				sys.exit('Unexpected wanted page format.')

			try:
				data = json.loads(match.group(1))
			except:
				sys.exit('Invalid JSON found in wanted page.')

			# Assert expected data
			if not isinstance(data, dict) or not isinstance(data.get('wantedItems'), list):
				sys.exit('Unexpected JSON content in wanted page.')

			if not data['wantedItems']:
				# No items on this page
				break

			for row in data['wantedItems']:
				items.append({
					'type': row['itemType'],
					'id': row['itemNo'],
					'color': row['colorID'],
					'name': encode(row['itemName']),
					'condition': row['wantedNew'],
					'minquantity': row['wantedQty'],
					'maxprice': row['wantedPrice'],
					'remarks': encode(row['wantedRemark'] or ''),
					'notify': row['wantedNotify'],
				})

			if len(items) == data.get('totalResults'):
				break

		# See https://www.bricklink.com/help.asp?helpID=207
		print('<INVENTORY>')
		for item in items:	
			print('\t<ITEM>')
			print('\t\t<ITEMTYPE>%s</ITEMTYPE>' % item['type'])
			print('\t\t<ITEMID>%s</ITEMID>' % item['id'])
			if item['color']:
				print('\t\t<COLOR>%s</COLOR>' % item['color'])
			print('\t\t<CONDITION>%s</CONDITION>' % item['condition'])
			if item['maxprice'] > 0:
				print('\t\t<MAXPRICE>%s</MAXPRICE>' % item['maxprice'])
			if item['minquantity']:
				print('\t\t<MINQTY>%s</MINQTY>' % item['minquantity'])
			print('\t\t<REMARKS>%s</REMARKS>' % item['remarks'])
			print('\t\t<NOTIFY>%s</NOTIFY>' % item['notify'])
			print('\t\t<WANTEDLISTID>%d</WANTEDLISTID>' % (args.wanted if args.wanted is not None else args.export))
			print('\t</ITEM>')
		print('</INVENTORY>')
		
		sys.exit()
	
	parser.print_help()

if __name__ == '__main__':
	main()

