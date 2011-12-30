import os
import re
import flickr

class Photo:
  def __init__(self, path, data = None):
    self.path   = path
    self.title  = path.split('/')[-1][0:-4]
    self.size   = os.path.getsize(self.path)
    self.data   = data
    
  def upload(self, callback = None):
    photo_id  = flickr.upload_photo(self.path, self.title, callback)
    return photo_id
    
class Photoset:
  def __init__(self, dir, data = None):
    self.dir    = dir
    self.title  = dir.split('/')[-1]
    self.photos = []
    self.data   = data
    self.__load_dir(dir)
    
  def __load_dir(self, dir):
    for filename in os.listdir(dir):
      if os.path.isdir(dir + '/' + filename):
        self.__load_dir(dir + '/' + filename)
        
      if re.search('\.jpg', filename.lower()):
        self.photos.append(Photo(dir + '/' + filename))
    
  def size(self):
    return sum([photo.size for photo in self.photos])
    
  def upload(self, callback = None):
    '''
    the title should not be duplicated
    '''
    photoset_ids  = flickr.find_photoset_ids(self.title)
    photoset_id   = None
      
    uploaded_count    = 0
    for photo in self.photos:
      def __upload_callback(progress, done):
        callback(self, photo, progress, done)
      
      if callback: callback(self, photo, 0, False)  # begin upload
      photo_id  = photo.upload(__upload_callback if callback else None)
      uploaded_count  += 1
      if callback: callback(self, photo, 0, True)   # end upload
      
      print u"uploaded({0}/{1}): {2}({3:.2f} MB)".format(uploaded_count, len(self.photos), photo.title, photo.size / 1024 / 1024.)
      
      if photoset_id == None:
        if len(photoset_ids) > 0:
          photoset_id = photoset_ids[-1]  # choose latest photoset
        else:
          photoset_id = flickr.create_photoset(self.title, "", photo_id)
          continue
          
      flickr.add_photo(photoset_id, photo_id) # set photoset