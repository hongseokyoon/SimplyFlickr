import flickrapi
import os

def login():
  auth_url  = None
  
  if not Data.token:
    Data.flickr = flickrapi.FlickrAPI(Data.key, Data.secret)
    (Data.token, Data.frob, Data.nsid, auth_url) = Data.flickr.get_token_part_one(perms = 'write')

    if Data.token:
      Data.flickr = flickrapi.FlickrAPI(Data.key, Data.secret, Data.nsid, Data.token)
      
      return (True, None)
      
  return (False, auth_url)
  
def auth():
  (Data.token, Data.nsid) = Data.flickr.get_token_part_two((Data.token, Data.frob))

class Data:
  key     = '33726ac0a25ecf1ef45f889008fbf457'
  secret  = '58cc6410cf7a4883'

  flickr  = None
  frob    = None
  token   = None
  nsid    = None

  Photosets = []

class Photo:
  def __init__(self, id, title):
    self.id         = id
    self.title      = title
  
  @staticmethod
  def upload(path, callback):    
    rsp = Data.flickr.upload(path.encode('utf-8'), is_public = 0, callback = callback)
    photo_id  = rsp.find('photoid').text
    
    rsp   = Data.flickr.photos_getInfo(api_key = Data.key, photo_id = photo_id)
    title = rsp.find('photo').find('title').text
    
    return Photo(photo_id, title)
  
  def original_url(self):
    rsp = Data.flickr.photos_getSizes(api_key = Data.key, photo_id = self.id)
    for size in rsp.find('sizes').findall('size'):
      if size.attrib['label'] == 'Original':
        return size.attrib['source']
        
    return None
  
  def download(self, filename):
    import urllib
    web_file    = urllib.urlopen(self.original_url())
    print ">> download:", filename
    local_file  = open(filename, 'wb')
    local_file.write(web_file.read())
    web_file.close()
    local_file.close()
  
class Photoset:
  def __init__(self, id, primary, title, description):
    self.id           = id
    self.primary      = primary
    self.title        = title
    self.description  = description
    self.photos       = []
  
  @staticmethod
  def find(title):
    #return [photoset for photoset in Data.Photosets if photoset.title == title]
    for photoset in Data.Photosets:      
      if photoset.title == title:
        return photoset
    
    return None
  
  @staticmethod
  def create(title, photo):
    rsp = Data.flickr.photosets_create(api_key = Data.key, title = title, primary_photo_id = photo.id)
    photoset_id = rsp.find('photoset').attrib['id']
    
    rsp = Data.flickr.photosets_getInfo(api_key = Data.key, photoset_id = photoset_id)
    primary     = rsp.find('photoset').attrib['primary']
    title       = rsp.find('photoset').find('title').text
    description = rsp.find('photoset').find('description').text
    
    new_photoset  = Photoset(photoset_id, primary, title, description)
    Data.Photosets.append(new_photoset)
    # insert photo into new photoset
    # (as default, newaly created photoset has to have one photo)
    new_photoset.photos.append(photo)
    return new_photoset
    
  @staticmethod
  def __load_photos(flickr, api_key, photoset_id):
    page    = 1
    pages   = 0
    photos  = []

    while True:
      rsp = flickr.photosets_getPhotos(api_key = api_key, photoset_id = photoset_id, page = page)

      for photoset in rsp.findall('photoset'):
        if pages == 0:
          pages = int(photoset.attrib['pages'])

        for photo in photoset.findall('photo'):
          photos.append(Photo(photo.attrib['id'], photo.attrib['title']))

      if page == pages:
        break

      page  += 1

    return photos
    
  @staticmethod
  def __load_photosets(flickr, api_key, user_id, callback):
    photosets = []
    rsp = flickr.photosets_getList(api_key = api_key, user_id = user_id)

    total_photoset  = len(rsp.find('photosets').findall('photoset'))
    
    
    for photoset in rsp.find('photosets').findall('photoset'):      
      photosets.append(Photoset(photoset.attrib['id'], photoset.attrib['primary'], photoset.find('title').text, photoset.find('description').text))

      if callback:
        callback(len(photosets), total_photoset, photosets[-1], False)

      # load photos in photoset
      photosets[-1].photos  = Photoset.__load_photos(flickr, api_key, photosets[-1].id)

      if callback:
        callback(len(photosets), total_photoset, photosets[-1], True)
        
    return photosets
    
  @staticmethod
  def load(callback):
    print ">> load"
    
    Data.Photosets  = Photoset.__load_photosets(Data.flickr, Data.key, Data.nsid, callback)
  
  def add_photo(self, photo):
    Data.flickr.photosets_addPhoto(api_key = Data.key, photoset_id = self.id, photo_id = photo.id)
    self.photos.append(photo)
    
  def find_photo(self, title):
    for photo in self.photos:
      if photo.title == title:
        return photo
    
    return None
    
  def download(self, callback):
    for photo in self.photos:
      if callback: callback(self, photo, 0, False)
      
      # each images are downloaded into the directory named after its title of photoset
      path  = self.title + "/" + photo.title + ".jpg"
      if not os.path.exists(self.title):
        os.makedirs(self.title)
      if not os.path.exists(path):
        photo.download(path)
        
      if callback: callback(self, photo, 100, True)