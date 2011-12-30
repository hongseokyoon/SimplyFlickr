import os
import flickr

class Photo:
  def __init__(self, id, title, data = None):
    self.id     = id
    self.title  = title
    self.data   = data
  
  def download(self, filename):
    import urllib
    web_file    = urllib.urlopen(flickr.photo_url(self.id))
    print ">> download:", filename
    local_file  = open(filename, 'wb')
    local_file.write(web_file.read())
    local_file.close()
    web_file.close()
  
class Photoset:
  def __init__(self, id, primary, title, description, data = None):
    self.id           = id
    self.primary      = primary
    self.title        = title
    self.description  = description
    self.photos       = []
    self.data         = data
  '''  
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
    page        = 1
    pages       = 0
    self.photos = []  # clear list first

    while True:
      rsp = flickr.photosets_getPhotos(api_key = api_key, photoset_id = photoset_id, page = page)

      for photoset in rsp.findall('photoset'):
        if pages == 0:
          pages = int(photoset.attrib['pages'])

        for photo in photoset.findall('photo'):
          self.photos.append(Photo(photo.attrib['id'], photo.attrib['title']))

      if page == pages:
        break

      page  += 1

    return photos
    
  @staticmethod
  def find_ids(flickr, api_key, user_id, title):
    photoset_ids  = []
    
    rsp = flickr.photosets_getList(api_key = api_key, user_id = user_id)
    for photoset in rsp.find('photosets').findall('photoset'):
      if photoset.find('title').text == title:
        photoset_ids.append(photoset.attrib['id'])
        
    return photoset_ids
    
  @staticmethod
  def load(flickr, api_key, user_id, callback):
    photosets = []  # list of remote.Photoset
    
    rsp = flickr.photoset_getList(api_key = api_key, user_id = user_id)
    total_photoset  = len(rsp.find('photosets').findall('photoset'))
    
    for photoset in rsp.find('photosets').findall('photoset'):
      remote_photoset = Photoset(photoset.attrib['id'], photoset.attrib['primary'], photoset.find('title').text, photoset.find('description').text)
      
      if callback: callback(len(photosets), total_photoset, remote_photoset, False) # begin
      remote_photoset.load_photos(flickr, api_key, user_id)
      if callback: callback(len(photosets), total_photoset, remote_photoset, True)  # end
      
      photosets.append(remote_photoset)
      
    return photosets
  
  def load_photos(flickr, api_key, user_id):
    page        = 1
    pages       = 0
    self.photos = []

    while True:
      rsp = flickr.photosets_getPhotos(api_key = api_key, photoset_id = self.id, page = page)

      for photoset in rsp.findall('photoset'):
        if pages == 0:
          pages = int(photoset.attrib['pages']) # save total number of pages

        for photo in photoset.findall('photo'):
          self.photos.append(Photo(photo.attrib['id'], photo.attrib['title']))

      if page == pages:
        break

      page  += 1  # check next page
    
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
  '''    
  def download(self, callback):
    for photo in self.photos:
      if callback: callback(self, photo, 0, False)  # begin download
      
      # each images are downloaded into the directory named after its title of photoset
      path  = self.title + "/" + photo.title + ".jpg"
      if not os.path.exists(self.title):
        os.makedirs(self.title)
      if not os.path.exists(path):
        photo.download(path)
        
      if callback: callback(self, photo, 100, True) # end download