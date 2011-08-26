import os
import re
import flickr

class Photo:
  def __init__(self, path):
    self.path     = path
    self.title    = path.split('/')[-1][0:-4]
    self.size     = os.path.getsize(self.path)
    
  def upload(self, callback = None):
    return flickr.Photo.upload(self.path, callback)
    
class Photoset:
  def __init__(self, dir):
    self.dir    = dir
    self.title  = dir.split('/')[-1]
    self.photos = []
    self.__load_dir(dir)
    
  def __load_dir(self, dir):
    for filename in os.listdir(dir):
      if os.path.isdir(dir + '/' + filename):
        self.__load_dir(dir + '/' + filename)
        
      if re.search('\.jpg', filename.lower()):
        self.photos.append(Photo(dir + '/' + filename))
    
  def size(self):
    total_size  = 0
    for photo in self.photos:
      total_size  += photo.size
      
    return total_size
    
  def upload(self, callback = None):
    flickr_photoset = flickr.Photoset.find(self.title)
    
    for photo in self.photos:
      def __upload_callback(progress, done):
        callback(self, photo, progress, done)
      
      if flickr_photoset and flickr_photoset.find_photo(photo.title):
        print 'duplicated photo:', photo.__dict__
        continue
      
      if callback: callback(self, photo, 0, False)
      flickr_photo  = photo.upload(__upload_callback if callback else None)
      if callback: callback(self, photo, 0, True)
      
      if not flickr_photoset:
        flickr_photoset = flickr.Photoset.create(self.title, flickr_photo)
      else:
        flickr_photoset.add_photo(flickr_photo)