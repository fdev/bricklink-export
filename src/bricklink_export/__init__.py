#!/usr/bin/env python

from __future__ import print_function

import itertools
import argparse
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
	parser.add_argument('--version', action='version', version='bricklink-export 1.0')
	parser.add_argument('-v', '--verbose', dest='verbose', action='store_true', default=False, help='be verbose')
	parser.add_argument('-u', '--username', dest='username', help='username on BrickLink')
	parser.add_argument('-p', '--password', dest='password', help='password on BrickLink (omit for prompt)')
	parser.add_argument('-l', '--list', dest='list', action='store_true', default=False, help='list of wanted lists')
	parser.add_argument('-c', '--colors', dest='colors', action='store_true', default=False, help='list of colors')
	parser.add_argument('-e', '--export', dest='export', metavar='ID', type=int, help='wanted list to export')
	args = parser.parse_args()
	
	# Requests session
	session = requests.Session()
	session.headers.update({'User-Agent': 'bricklink-export 1.0 (http://github.com/fdev/bricklink-export)'})
	
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
			'a': 'a',
			'logFrmFlag': 'Y',
			'frmUsername': username, 
			'frmPassword': password, 
		}
		r = session.post('https://www.bricklink.com/login.asp', data=payload, allow_redirects=False)

		if not r:
			sys.exit('Could not log in to BrickLink.')

		if r.status_code != 302 or r.headers['location'] != '/pageRedirect.asp?p=my.asp':
			sys.exit('Invalid username or password specified.')

		verbose('Authenticated as %s.' % username)

	# Fetch list of colors for color list and export
	if args.colors or args.export is not None:
		colors = []
		
		verbose('Retrieving color guide.')
		r = session.get('http://www.bricklink.com/catalogColors.asp')
		if not r:
			sys.exit('Could not retrieve color guide.')

		verbose('Parsing.')
		html = pq(r.text)
		tables = html('table tr')
	
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
	
	# Color list
	if args.colors:
		print('ID\tName')
		for color in colors:
			print('%s\t%s' % (color['id'], color['name']))
		sys.exit()
	
	# List of wanted lists
	if args.list:
		verbose('Retrieving list of wanted lists.')
		r = session.get('http://www.bricklink.com/wantedView.asp')
		if not r:
			sys.exit('Could not retrieve wanted lists.')

		verbose('Parsing.')
		html = pq(r.text)
		table = html('form[action="wantedView.asp?a=md"]').closest('table')
		header = table('tr:eq(0)')
		rows = table('tr:gt(0)')
	
		# Assert expected header
		for col, label in enumerate(('ID', 'Name', 'Items')):
			td = strip(header('td:eq(%d)' % col).text())
			if td != label:
				sys.exit('Unexpected wanted list table format.')
	
		# Print list
		print('ID\tItems\tName')
		for row in map(pq, rows):
			id = row('td:eq(0)').text().strip()
			if row('td:eq(1) input'):
				name = row('td:eq(1) input:first').attr('value')
			else:
				# First row is static
				name = row('td:eq(1)').text().strip()
			items = row('td:eq(2)').text().strip() or '0'

			print('%s\t%s\t%s' % (id, items, name))
	
		sys.exit()

	# Export
	if args.export is not None:
		items = []
	
		# Sort colors by name length (longest first)
		itemcolors = sorted(colors, key=lambda color: len(color['name']), reverse=True)
		
		# The wanted list is split per item type
		itemtypes = (
			('S', 'sets'),
			('P', 'parts'),
			('M', 'minifigs'),
			('B', 'books'),
			('G', 'gear'),
			('C', 'catalogs'),
			('I', 'instructions'),
			('O', 'original boxes'),
			('U', 'unsorted'),
		)

		for itemtype, name in itemtypes:
			for page in itertools.count(1):
				verbose('Retrieving page %d of item type %s...' % (page, name))
				payload = {
					'pg': page,
					'catType': itemtype,
					'wantedMoreID': args.export,
				}
				r = session.get('http://www.bricklink.com/wantedDetail.asp', params=payload)
				if not r:
					sys.exit('Could not retrieve page %d of part list.' % page)

				verbose('Parsing.')
				html = pq(r.text)
				form = html('form[name="wantedForm"]')
				
				if not form:
					# No items on this page
					break

				table = form.closest('table')
				header = table('tr:eq(0)')
				rows = table.find('tr:gt(0)')
	
				# Assert expected header
				for col, label in enumerate(('Image', 'Notify', 'Condition', 'Min Qty', 'Max Price', 'My Remarks')):
					td = strip(header('td:eq(%d)' % col).text())
					if td != label:
						sys.exit('Unexpected wanted list table format.')
	
				if len(rows) % 4 != 0:
					sys.exit('Unexpected wanted list table length.')

				for row1, row2, row3, row4 in zip(*([iter(map(pq, rows))] * 4)):
					# Part number
					link = row1('td:eq(2) a[href]').attr('href')
					match = re.match('^catalogItem.asp\?[SPMBGCIOU]=([0-9a-zA-Z\-]+)', link)
					if not match:
						sys.exit('Unexpected wanted list item link format.')
					item = match.group(1)
		
					# Part name
					name = row1('td:eq(2)').text().strip()
		
					# Notify
					notify = 'Y' if row2("td:eq(0) input[type='CHECKBOX']").attr('checked') else 'N'
				
					# Condition
					condition = row2("td:eq(1) input[type='hidden']").attr('value')
		
					# Minimum quantity
					minquantity = row2("td:eq(2) input[type='hidden']").attr('value')
		
					# Maximum price
					maxprice = row2("td:eq(3) input[type='hidden']").attr('value')
		
					# Remarks
					remarks = row2("td:eq(6) input[type='TEXT']").attr('value')

					# Color (only for parts)
					color = None
					if itemtype == 'P':
						for itemcolor in itemcolors:
							# Name starts with color name.
							if name.startswith(itemcolor['name'] + ' '):
								color = itemcolor['id']
								break
		
					items.append({
						'type': itemtype,
						'id': item,
						'color': color,
						'name': encode(name),
						'condition': condition,
						'minquantity': minquantity,
						'maxprice': maxprice,
						'remarks': encode(remarks),
						'notify': notify,
					})
				
				if not html("a[href]:contains('Next')"):
					break
		
		# See http://www.bricklink.com/help.asp?helpID=207
		print('<INVENTORY>')
		for item in items:	
			print('\t<ITEM>')
			print('\t\t<ITEMTYPE>%s</ITEMTYPE>' % item['type'])
			print('\t\t<ITEMID>%s</ITEMID>' % item['id'])
			if item['color']:
				print('\t\t<COLOR>%s</COLOR>' % item['color'])
			print('\t\t<CONDITION>%s</CONDITION>' % item['condition'])
			if item['maxprice']:
				print('\t\t<MAXPRICE>%s</MAXPRICE>' % item['maxprice'])
			if item['minquantity']:
				print('\t\t<MINQTY>%s</MINQTY>' % item['minquantity'])
			print('\t\t<REMARKS>%s</REMARKS>' % item['remarks'])
			print('\t\t<NOTIFY>%s</NOTIFY>' % item['notify'])
			print('\t</ITEM>')
		print('</INVENTORY>')
		
		sys.exit()
	
	parser.print_help()

if __name__ == '__main__':
	main()

