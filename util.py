import urllib
import urllib2
import requests
from random import Random
from threading import Timer

image_temp_dir = '/data/tmp/image/'

def random_str(randomlength=8):
	str = ''
	chars = 'AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz0123456789'
	length = len(chars) - 1
	random = Random()
	for i in range(randomlength):
	    str+=chars[random.randint(0, length)]
	return str

def get_image(url, filename=''):
	if filename == '':
		filename = random_str(4) + ".jpg"
	filepath = image_temp_dir + filename
	f = urllib2.urlopen(url, timeout=5)
	t = Timer(5.0, f.close)
	t.start()
	try:
		data = f.read()
	except AttributeError:
		return '00000.jpg'
	with open(filepath, "wb") as code:
		code.write(data)
	return filepath
