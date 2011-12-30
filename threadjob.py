import threading
import wx
import local
import remote
import flickr
from wx.lib.pubsub import Publisher

class StoppableThread(threading.Thread):
  def __init__(self):
    threading.Thread.__init__(self)
    self._stop = threading.Event()

  def stop(self):
    print "stop"
    if self.isAlive() == True:
      self._stop.set()
      self.join()
      print "stopped"

class LoadLocalPhotoset(StoppableThread):
  def __init__(self, dir):
    StoppableThread.__init__(self)
    self.dir  = dir
    self.start()
    
  def run(self):
    try:
      photoset  = local.Photoset(self.dir)
      Publisher().sendMessage(('LoadLocalPhotoset'), photoset)
    except wx.PyDeadObjectError:
      pass

class UploadLocalPhotosets(StoppableThread):
  def __init__(self, photosets, callback = None):
    '''
    callback(local.Photoset, local.Photo, progress, done)
    '''
    StoppableThread.__init__(self)
    self.photosets  = photosets
    self.callback   = callback
    self.start()
    
  def run(self):
    try:
      for photoset in self.photosets:
        photoset.upload(self.callback)
        
      Publisher().sendMessage(('UploadLocalPhotosets'), self.photosets)
    except wx.PyDeadObjectError:
      pass

class LoadRemotePhotosets(StoppableThread):
  def __init__(self):
    StoppableThread.__init__(self)
    self.start()
    
  def run(self):
    photosets = []
    
    try:
      for photoset_info in flickr.load_photosets():
        photoset  = remote.Photoset(photoset_info['id'], photoset_info['primary'], photoset_info['title'], photoset_info['description'])
        for photo_info in flickr.load_photos(photoset.id):
          photoset.photos.append(remote.Photo(photo_info['id'], photo_info['title']))
          
        photosets.append(photoset)
        Publisher().sendMessage(('LoadRemotePhotoset'), photoset)
      
      Publisher().sendMessage(('LoadRemotePhotosets'), photosets)
    except wx.PyDeadObjectError:
      pass
      
class DownloadRemotePhotosets(StoppableThread):
  def __init__(self, photosets, callback = None):
    '''
    callback(remote.Photoset, remote.Photo, progress, done)
    '''
    StoppableThread.__init__(self)
    
    self.photosets  = photosets
    self.callback   = callback
    self.start()
    
  def run(self):
    try:
      for photoset in self.photosets:
        photoset.download(self.callback)
      Publisher().sendMessage(('DownloadRemotePhotosets'), self.photosets)
    except wx.PyDeadObjectError:
      pass