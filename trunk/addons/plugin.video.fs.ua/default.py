#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#   Writer (c) 23/06/2011, Khrysev D.A., E-mail: x86demon@gmail.com
#
#   This Program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 2, or (at your option)
#   any later version.
#
#   This Program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program; see the file COPYING.  If not, write to
#   the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#   http://www.gnu.org/licenses/gpl.html

import urllib
import urllib2
import re
import sys
import os
import cookielib

import xbmcplugin
import xbmcgui
import xbmcaddon
import xbmc

from BeautifulSoup import BeautifulSoup, BeautifulStoneSoup
import socket
socket.setdefaulttimeout(50)

icon = xbmc.translatePath(os.path.join(os.getcwd().replace(';', ''), 'icon.png'))
siteUrl = 'fs.ua'
httpSiteUrl = 'http://' + siteUrl
__settings__ = xbmcaddon.Addon(id='plugin.video.fs.ua')
__language__  = __settings__.getLocalizedString
cookiepath = os.path.join(xbmc.translatePath('special://temp/'), 'plugin.video.fs.ua.cookies.lwp')

h = int(sys.argv[1])

def construct_request(params):
	return '%s?%s' % (sys.argv[0], urllib.urlencode(params))

def htmlEntitiesDecode(string):
	return BeautifulStoneSoup(string, convertEntities=BeautifulStoneSoup.HTML_ENTITIES).contents[0]

def showMessage(heading, message, times = 3000):
	xbmc.executebuiltin('XBMC.Notification("%s", "%s", %s, "%s")'%(heading, message, times, icon))

headers  = {
	'User-Agent' : 'Opera/9.80 (X11; Linux i686; U; ru) Presto/2.7.62 Version/11.00',
	'Accept'     :' text/html, application/xml, application/xhtml+xml, image/png, image/jpeg, image/gif, image/x-xbitmap, */*',
	'Accept-Language':'ru-RU,ru;q=0.9,en;q=0.8',
	'Accept-Charset' :'utf-8, utf-16, *;q=0.1',
	'Accept-Encoding':'identity, *;q=0'
}

def GET(url, referer, post_params = None):
	headers['Referer'] = referer

	if post_params != None:
		post_params = urllib.urlencode(post_params)
		headers['Content-Type'] = 'application/x-www-form-urlencoded'
	elif headers.has_key('Content-Type'):
		del headers['Content-Type']

	jar = cookielib.LWPCookieJar(cookiepath)
	if os.path.isfile(cookiepath):
		jar.load()

	opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(jar))
	urllib2.install_opener(opener)
	req = urllib2.Request(url, post_params, headers)

	response = opener.open(req)
	the_page = response.read()
	response.close()

	jar.save()

	return the_page

def check_login():
	login = __settings__.getSetting("Login")
	password = __settings__.getSetting("Password")

	if len(login) > 0:
		http = GET(httpSiteUrl, httpSiteUrl)
		if http == None: return False

		beautifulSoup = BeautifulSoup(http)
		userPanel = beautifulSoup.find('div', 'b-user-panel')

		if userPanel == None:
			os.remove(cookiepath)
			
			loginResponse = GET(httpSiteUrl + '/login.aspx', httpSiteUrl, {
				'login': login,
				'passwd': password,
				'remember': 1
			})

			loginSoup = BeautifulSoup(loginResponse)
			userPanel = loginSoup.find('div', 'b-user-panel')
			if userPanel == None:
				showMessage('Login', 'Check login and password', 3000)
			else:
				return True
		else:
			return True
	return False

def getSortBy():
	sortBy = __settings__.getSetting("Sort by")
	sortByMap = {'0': 'new', '1': 'rating', '2': 'year'}
	return '?view=list&sort=' + sortByMap[sortBy]

def main(params):
	li = xbmcgui.ListItem('Видео')
	uri = construct_request({
		'href': httpSiteUrl + '/video/',
		'mode': 'getCategories',
		'category': 'video',
		'filter': '',
		'firstPage': 'yes'
	})
	xbmcplugin.addDirectoryItem(h, uri, li, True)

	li = xbmcgui.ListItem('Аудио')
	uri = construct_request({
		'href': httpSiteUrl + '/audio/',
		'mode': 'getCategories',
		'category': 'audio',
		'filter': '',
		'firstPage': 'yes'
	})
	xbmcplugin.addDirectoryItem(h, uri, li, True)

	if check_login():
		li = xbmcgui.ListItem('Избранное')
		uri = construct_request({
			'mode': 'getFavoriteCategories',
			'type': 'favorites'
		})
		xbmcplugin.addDirectoryItem(h, uri, li, True)

		li = xbmcgui.ListItem('Рекомендуемое')
		uri = construct_request({
			'mode': 'getFavoriteCategories',
			'type': 'recommended'
		})
		xbmcplugin.addDirectoryItem(h, uri, li, True)

		li = xbmcgui.ListItem('К просмотру')
		uri = construct_request({
			'mode': 'getFavoriteCategories',
			'type': 'playlist'
		})
		xbmcplugin.addDirectoryItem(h, uri, li, True)

		li = xbmcgui.ListItem('Просмотенное')
		uri = construct_request({
			'mode': 'getFavoriteCategories',
			'type': 'viewed'
		})
		xbmcplugin.addDirectoryItem(h, uri, li, True)

	xbmcplugin.endOfDirectory(h)

def getCategories(params):
	sortByString = getSortBy()
	section = params['category']
	categoryUrl = urllib.unquote_plus(params['href'])

	http = GET(categoryUrl, httpSiteUrl)
	if http == None: return False

	beautifulSoup = BeautifulSoup(http)
	topMenu = beautifulSoup.find('ul', 'b-header-menu')

	if topMenu == None:
		showMessage('ОШИБКА', 'Неверная страница', 3000)
		return False
	categorySubmenu = topMenu.find('li', 'm-%s' % section)
	if categorySubmenu == None:
		showMessage('ОШИБКА', 'Неверная страница', 3000)
		return False

	subcategories = categorySubmenu.findAll('a')
	if len(subcategories) == 0:
		showMessage('ОШИБКА', 'Неверная страница', 3000)
		return False
	for subcategory in subcategories:
		li = xbmcgui.ListItem(subcategory.string)
		uri = construct_request({
			'href': httpSiteUrl + subcategory['href'] + sortByString,
			'mode': 'readcategory',
			'section': section,
			'filter': '',
			'firstPage': 'yes'
		})
		xbmcplugin.addDirectoryItem(h, uri, li, True)

	xbmcplugin.endOfDirectory(h)

def getFavoriteCategories(params):
	http = GET(httpSiteUrl + '/myfavourites.aspx?page=' + params['type'], httpSiteUrl)
	if http == None: return False

	beautifulSoup = BeautifulSoup(http)
	favSectionsContainer = beautifulSoup.find('ul', 'b-fav-sections-list')
	if favSectionsContainer == None:
		showMessage('ОШИБКА', 'В избранном пусто', 3000)
		return False

	favSections = favSectionsContainer.findAll('li')
	if len(favSections) == 0:
		showMessage('ОШИБКА', 'В избранном пусто', 3000)
		return False
	for favSection in favSections:
		link = favSection.find('a')
		title = str(link.string)
		li = xbmcgui.ListItem(title)

		uri = construct_request({
			'mode': 'readfavorites',
			'href': httpSiteUrl + link['href']
		})
		xbmcplugin.addDirectoryItem(h, uri, li, True)
	xbmcplugin.endOfDirectory(h)

def readfavorites(params):
	favoritesUrl = urllib.unquote_plus(params['href'])

	http = GET(favoritesUrl, httpSiteUrl)
	if http == None: return False

	beautifulSoup = BeautifulSoup(http)
	itemsContainer = beautifulSoup.find('div', 'b-posters')
	if itemsContainer == None:
		showMessage('ОШИБКА', 'В избранном пусто', 3000)
		return False
	items = itemsContainer.findAll('a')
	if len(items) == 0:
		showMessage('ОШИБКА', 'В избранном пусто', 3000)
		return False
	else:
		coverRegexp = re.compile('url\s*\(([^\)]+)')
		for item in items:
			cover = coverRegexp.findall(str(item['style']))[0]
			title = str(item.find('span').string)
			href = httpSiteUrl + item['href']

			isMusic = "no"
			if re.search('audio', href):
				isMusic = "yes"

			li = xbmcgui.ListItem(htmlEntitiesDecode(title), iconImage = cover)
			li.setProperty('IsPlayable', 'false')

			id = item['href'].split('/')[-1]
			li.addContextMenuItems([
				(
					__language__( 50003 ), "XBMC.RunPlugin(%s)" % construct_request({
						'mode': 'addto',
						'section': 'favorites',
						'id': id,
						'title': title
					})
				),
				(
					__language__( 50004 ), "XBMC.RunPlugin(%s)" % construct_request({
						'mode': 'addto',
						'section': 'playlist',
						'id': id,
						'title': title
					})
				)
			])

			uri = construct_request({
				'href': href,
				'referer': href,
				'mode': 'readdir',
				'cover': cover,
				'folder': 0,
				'isMusic': isMusic
			})
			xbmcplugin.addDirectoryItem(h, uri, li, True)

	xbmcplugin.endOfDirectory(h)

def readcategory(params):
	sortByString = getSortBy()
	categoryUrl = urllib.unquote_plus(params['href'])
	http = GET(categoryUrl + sortByString, httpSiteUrl)
	if http == None: return False

	beautifulSoup = BeautifulSoup(http)
	items = beautifulSoup.findAll('a', 'subject-link')

	if len(items) == 0:
		showMessage('ОШИБКА', 'Неверная страница', 3000)
		return False
	else:
		if params['firstPage'] == 'yes':
			#Add search list item
			li = xbmcgui.ListItem("[ПОИСК]")
			li.setProperty('IsPlayable', 'false')
			uri = construct_request({
				'mode': 'runsearch',
				'section': params['section']
			})
			xbmcplugin.addDirectoryItem(h, uri, li, True)

		for item in items:
			title = None
			cover = None
			href = None

			img = item.find('img')
			if img != None:
				cover = img['src']
				title = img['alt']
				href = httpSiteUrl + item['href']

			if title != None:
				li = xbmcgui.ListItem(htmlEntitiesDecode(title), iconImage = cover)
				li.setProperty('IsPlayable', 'false')

				id = str(item['href'].split('/')[-1])
				li.addContextMenuItems([
					(
						__language__( 50001 ), "XBMC.RunPlugin(%s)" % construct_request({
							'mode': 'addto',
							'section': 'favorites',
							'id': id
						})
					),
					(
						__language__( 50002 ), "XBMC.RunPlugin(%s)" % construct_request({
							'mode': 'addto',
							'section': 'playlist',
							'id': id
						})
					)
				])

				isMusic = 'no'
				if params['section'] == 'audio':
					isMusic = 'yes'

				uri = construct_request({
					'href': href,
					'referer': categoryUrl,
					'mode': 'readdir',
					'cover': cover,
					'folder': 0,
					'isMusic': isMusic
				})

				xbmcplugin.addDirectoryItem(h, uri, li, True)

	nextPageLink = beautifulSoup.find('a', 'next-link')
	if nextPageLink != None:
		li = xbmcgui.ListItem('[NEXT PAGE >]')
		li.setProperty('IsPlayable', 'false')
		uri = construct_request({
			'href': httpSiteUrl + nextPageLink['href'],
			'mode': 'readcategory',
			'section': params['section'],
			'filter': params['filter'],
			'firstPage': 'no'
		})
		xbmcplugin.addDirectoryItem(h, uri, li, True)

	xbmcplugin.endOfDirectory(h)

def readdir(params):
	folderUrl = urllib.unquote_plus(params['href'])
	cover = urllib.unquote_plus(params['cover'])
	folder = params['folder']

	http = GET(folderUrl + '?ajax&folder=' + folder, httpSiteUrl)
	if http == None: return False

	beautifulSoup = BeautifulSoup(http)
	mainItems = beautifulSoup.find('ul', 'filelist')
	if mainItems == None:
		showMessage('ОШИБКА', 'No filelist', 3000)
		return False

	items = mainItems.findAll('li')

	folderRegexp = re.compile('\?folder=(\d+)#')
	if len(items) == 0:
		showMessage('ОШИБКА', 'Неверная страница', 3000)
		return False
	else:
		for item in items:
			isFolder = item['class'] == 'folder'
			linkItem = None
			playLink = None
			if isFolder:
				linkItem = item.find('a', 'title')
			else:
				linkItem = item.find('a', 'link-material')
				playLink = item.find('a', 'b-player-link')
			
			if linkItem != None:
				title = ""
				if isFolder:
					titleB = linkItem.find('b')
					if titleB == None:
						title = str(linkItem.string)
					else:
						title = str(titleB.string)
					quality = item.findAll('span', 'material-size')
					if len(quality) > 1:
						 title = title + " [" + str(quality[0].string) + "]"
				else:
					title = str(linkItem.find('span').string)

				useFlv = __settings__.getSetting('Use flv files for playback') == 'true'
				if useFlv and playLink != None:
					href = httpSiteUrl + str(playLink['href'])
				else:
					href = linkItem['href']
					try:
						folder = folderRegexp.findall(href)[0]
					except:
						pass

				li = None
				uri = None
				if isFolder:
					li = xbmcgui.ListItem(htmlEntitiesDecode(title), iconImage = cover)
					li.setProperty('IsPlayable', 'false')

					uri = construct_request({
						'cover': cover,
						'href': folderUrl,
						'referer': folderUrl,
						'mode': 'readdir',
						'folder': folder,
						'isMusic': params['isMusic']
					})
				else:
					li = xbmcgui.ListItem(htmlEntitiesDecode(title), iconImage = cover, path = href)
					li.setProperty('IsPlayable', 'true')
					type = 'video'
					if params['isMusic'] == 'yes':
						type = 'music'
					li.setInfo(type = type, infoLabels={'title': title})
					li.addContextMenuItems([
						(
							__language__( 40001 ), "XBMC.RunPlugin(%s)" % construct_request({
								'mode': 'download',
								'file_url': href
							})
						)
					])

					if type == 'music' or (__settings__.getSetting('Autoplay next') == 'true' and not useFlv):
						uri = construct_request({
							'file': str(href.encode('utf-8')),
							'referer': folderUrl,
							'mode': 'play'
						})
					elif useFlv:
						uri = construct_request({
							'file': href,
							'referer': folderUrl,
							'mode': 'playflv'
						})
					else:
						uri = href

				xbmcplugin.addDirectoryItem(h, uri, li, isFolder)

	xbmcplugin.endOfDirectory(h)

def runsearch(params):
	skbd = xbmc.Keyboard()
	skbd.setHeading('Что ищем?')
	skbd.doModal()
	if skbd.isConfirmed():
		SearchStr = skbd.getText()
		searchUrl = '%s/%s/search/?search=%s' % (httpSiteUrl, params['section'], urllib.quote_plus(SearchStr))
		params = {
			'href': searchUrl,
			'section': params['section']
		}
		return render_search_results(params)


def render_search_results(params):
	searchUrl = urllib.unquote_plus(params['href'])
	http = GET(searchUrl, httpSiteUrl + '/' + params['section'])
	if http == None: return False

	beautifulSoup = BeautifulSoup(http)
	items = beautifulSoup.find('div', 'main').findAll('tr')

	if len(items) == 0:
		showMessage('ОШИБКА', 'Ничего не найдено', 3000)
		return False
	else:
		for item in items:
			link = item.find('a', 'title')

			title = link.string
			href = httpSiteUrl + '/dl' + link['href']
			cover = item.find('img')['src']

			if title != None:
				li = xbmcgui.ListItem(htmlEntitiesDecode(title), iconImage = cover)
				li.setProperty('IsPlayable', 'false')

				isMusic = 'no'
				if params['section'] == 'music':
					isMusic = 'yes'

				uri = construct_request({
					'href': href,
					'referer': params['href'],
					'mode': 'readdir',
					'cover': cover,
					'isMusic': isMusic
				})

				xbmcplugin.addDirectoryItem(h, uri, li, True)

		nextPageLink = beautifulSoup.find('a', 'next-link')
		if nextPageLink != None:
			li = xbmcgui.ListItem('[NEXT PAGE >]')
			li.setProperty('IsPlayable', 'false')
			uri = construct_request({
				'href': httpSiteUrl + nextPageLink['href'],
				'mode': 'render_search_results',
				'section': params['section']
			})
			xbmcplugin.addDirectoryItem(h, uri, li, True)

	xbmcplugin.endOfDirectory(h)

def addto(params):
	addToHref = httpSiteUrl + "/addto/" + params['section'] + '/' + params['id'] + "?json"
	GET(addToHref, httpSiteUrl)
	showMessage('Result', "Toggled state in " + params['section'], 5000)

def playflv(params):
	referer = urllib.unquote_plus(params['referer'])
	file = urllib.unquote_plus(params['file'])
	http = GET(file, referer)
	if http == None: return False

	beautifulSoup = BeautifulSoup(http)
	playerLink = beautifulSoup.findAll('a', attrs={'id': "player"})
	if playerLink == None:
		showMessage('Error', 'FLV file was not found')
		return False

	file = urllib.urlopen(str(playerLink[0]['href']))
	fileUrl = file.geturl()

	i = xbmcgui.ListItem(path = fileUrl)
	xbmcplugin.setResolvedUrl(h, True, i)

def play(params):
	referer = urllib.unquote_plus(params['referer'])
	file = urllib.unquote_plus(params['file'])
	headers['Referer'] = referer

	file = urllib.urlopen(file)
	fileUrl = file.geturl()

	i = xbmcgui.ListItem(path = fileUrl)
	xbmcplugin.setResolvedUrl(h, True, i)

def download(params):
	file_url = urllib.unquote_plus(params['file_url'])
	file_name = ''.join(file_url.split('/')[-1:])

	dialog = xbmcgui.Dialog()
	file_path = dialog.browse(0, __language__( 40002 ), 'myprograms')

	if file_path:
		try:
			filename_complete = file_path + file_name
			filename_incomplete = file_path + file_name + '.part'

			dp = xbmcgui.DialogProgress()
			dp.create("FS.UA",__language__( 40003 ),file_name)
			urllib.urlretrieve(file_url,filename_incomplete,lambda nb, bs, fs, url=file_url: _progress_bar_hook(nb,bs,fs,url,dp))

			os.rename(filename_incomplete, filename_complete)

			showMessage(__language__( 40004 ), filename_complete, )
		except:
				showMessage(__language__( 40005 ), file_name, 3000)
				if os.path.isfile(filename_incomplete):
					os.remove(filename_incomplete)

def _progress_bar_hook(numblocks, blocksize, filesize, url=None, dp=None):
	try:
		percent = min((numblocks*blocksize*100)/filesize, 100)
		total = '%s (%s %s)' %(__language__( 40003 ), str(filesize/1024/1024),  __language__( 40006 ))
		dp.update(percent,total)
	except:
		percent = 100
		dp.update(percent)
	if dp.iscanceled():
		dp.close()

def get_params(paramstring):
	param=[]
	if len(paramstring)>=2:
		params=paramstring
		cleanedparams=params.replace('?','')
		if (params[len(params)-1]=='/'):
			params=params[0:len(params)-2]
		pairsofparams=cleanedparams.split('&')
		param={}
		for i in range(len(pairsofparams)):
			splitparams={}
			splitparams=pairsofparams[i].split('=')
			if (len(splitparams))==2:
				param[splitparams[0]]=splitparams[1]
	return param

params = get_params(sys.argv[2])

mode   = None
func   = None

try:
	mode = urllib.unquote_plus(params['mode'])
except:
	main(params)

if (mode != None):
	try:
		func = globals()[mode]
	except:
		pass
	if func: func(params)
