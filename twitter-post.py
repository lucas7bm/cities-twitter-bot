from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup as Soup
from random import randint
from multiprocessing import Pool, cpu_count
import os, ast, requests, time, datetime, imghdr, tweepy

consumer_key = ""
consumer_secret = ""
access_key = ""
access_secret = ""

chrome_options = Options()  
chrome_options.add_argument("--headless")  

driver = webdriver.Chrome("./chromedriver.exe", options=chrome_options)

def get_random_image():
  f = open("cities.csv", encoding="utf8")
  cities = []
  for line in f:
    cities.append(line.replace("\n", ""))
  
  index = randint(0, len(cities) - 1)
  return cities[index]

def download_picture(line):
  data = line.replace('\n', ' ').split(',')
  city = data[0]
  country = data[1]
  query = city + " city of " + country
  print("Downloading image of " + query + "...")
  url = 'https://www.google.com/search?q=' + query.replace(' ', '+') + '&tbm=isch'

  driver.get(url)
  page = driver.page_source
  print(" - Page downloaded.")
  
  soup = Soup(page, 'lxml')
  url_divs = soup.find_all('div', {'class':'rg_meta notranslate'}, limit=20)
  time.sleep(1)

  if len(url_divs) == 0:
    print("Trying again, no divs...")
    return download_picture(line)
  print(" - Divs extracted")

  urls = []
  for i in url_divs:
    link = i.text
    link = ast.literal_eval(link)['ou']
    urls.append(link)

  print(" - URLs extracted.")

  randindex = randint(0, len(urls) - 1)
  image_url = urls[randindex]
  
  print(" - Random URL selected.")

  try:
    r = requests.get(image_url, timeout=5)
    image = r.content
    image_type = imghdr.what('', image)

    if image_type != "jpeg" or (len(image)) > 3072000:
      print("Trying again, not a JPEG or image size bigger than 3072KB...")
      return download_picture(line)
    
    f = open("image.jpg",'wb+')
    f.write(image)
    f.close()

    print(city + " - " + country + " downloaded.\n")

    return True
  except Exception as e:
    print("Trying again in 10 seconds, request error...")
    print(e)
    time.sleep(10)
    return download_picture(line)

def tweet(image_path, status):
  auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
  auth.set_access_token(access_key, access_secret)
  tw = tweepy.API(auth)
  try:
    tw.update_with_media(image_path, status)
    return True
  except Exception as e:
    time.sleep(10)
    print("Trying again, request error...")
    print(e)
    return tweet(image_path, status)
  
def tweet_random_image():
  image = get_random_image()
  data = image.split(",")
  if data[2] == "":
    data[2] = "0 (Maybe there is no data available)" 
  status = "City: " + data[0] + "\n" + "Country: " + data[1] + "\n" + "Population: " + data[2] + "\n" + "Latitude: " + data[3] + "\n" + "Longitude: " + data[4] + "\n"
  if download_picture(image):
    if tweet("image.jpg", status):
      print(datetime.datetime.now())
      print(data[0] + " - " + data[1] + " was successfully posted.")
      f = open("posted-cities.log", "a+", encoding="utf8")
      f.write(data[0] + " - " + data[1] + "\n")
while(True):
  tweet_random_image()
  time.sleep(900)
