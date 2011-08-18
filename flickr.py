import flickrapi

class Data:
  key     = '33726ac0a25ecf1ef45f889008fbf457'
  secret  = '58cc6410cf7a4883'

  flickr  = None
  frob    = None
  token   = None
  nsid    = None

  Photosets = []

Photosets = None

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
    return new_photoset
    
  def add_photo(self, photo):
    Data.flickr.photosets_addPhoto(api_key = Data.key, photoset_id = self.id, photo_id = photo.id)

def __read_authinfo():
  try:
    f = open('.authinfo', 'r')
    Data.token, Data.nsid = f.readlines(2)
    Data.token = Data.token.strip()
    f.close()
  except IOError as e:
    raise e
    
  return True
  
def __write_authinfo():
  try:
    f = open('.authinfo', 'w')
    f.writelines([Data.token + '\n', Data.nsid])
    f.close()
  except IOError:
    return False
    
  return True
    
def __photos(photoset_id):
  rsp = Data.flickr.photosets_getPhotos(api_key = Data.key, photoset_id = photoset_id)
  
  photos  = []
  
  for photoset in rsp.findall('photoset'):
    for photo in photoset.findall('photo'):
      photos.append(Photo(photo.attrib['id']), photo.attrib['title'])
  
def __photosets():
  rsp = Data.flickr.photosets_getList(api_key = Data.key, user_id = Data.nsid)
  
  photosets = []
  
  for photoset in rsp.find('photosets').findall('photoset'):
    photosets.append(Photoset(photoset.attrib['id'], photoset.attrib['primary'], photoset.find('title').text, photoset.find('description').text))
    #photosets[-1].photos  = __photos(photosets[-1].id)
  
  return photosets
  
def login():
  global Photosets
  
  if Data.frob and not Data.token:
    Data.flickr = flickrapi.FlickrAPI(Data.key, Data.secret)
    rsp = Data.flickr.auth_getToken(api_key = Data.key, frob = Data.frob)
    Data.token  = rsp.find('auth').find('token').text
    Data.nsid   = rsp.find('auth').find('user').attrib['nsid']
    __write_authinfo()
  
  if not __read_authinfo():
    return False
    
  Data.flickr = flickrapi.FlickrAPI(Data.key, Data.secret, Data.nsid, Data.token)
  Photosets = Data.Photosets = __photosets()
  return True
  
def auth():  
  Data.flickr = flickrapi.FlickrAPI(Data.key, Data.secret)
  
  rsp         = Data.flickr.auth_getFrob(api_key = Data.key)
  Data.frob = rps.find('frob').text
  
  return Data.flickr.auth_url('write', Data.frob)