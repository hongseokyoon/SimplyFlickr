import threading
import local
import wx
#from wx.lib.pubsub import Publisher

class StoppableThread(threading.Thread):
  def __init__(self):
    super(StoppableThread, self).__init__()
    self._stop = threading.Event()

  def stop(self):
    self._stop.set()

  def stopped(self):
    return self._stop.isSet()
    
class AddPhotosetThread(StoppableThread):
  def __init__(self, dir, callback = None):
    '''
    callback(local.Photoset)
    '''
    StoppableThread.__init__(self)
    self.dir  = dir
    self.start()
    
  def run(self):
    try:    
      localPhotoset = local.Photoset(self.dir)
      callback(localPhotoset)
    except wx.PyDeadObjectError:
      pass
    
class UploadPhotosetsThread(StoppableThread):
  def __init__(self, localPhotosets, callback = None):
    '''
    callback(local.Photoset, local.Photo, progress, done)
    '''
    StoppableThread.__init__(self)
    self.localPhotosets = localPhotosets
    self.callback       = callback
    self.start()
    
  def run(self):
    try:
      for localPhotoset in self.localPhotosets:
        localPhotoset.upload(self.callback)
    except wx.PyDeadObjectError:
      pass
    
class LoadPhotosetsThread(StoppableThread):
  def __init__(self, flickr, callback = None):
    '''
    callback(photoset_num, total_photoset, flickr.Photoset, done)
    '''
    StoppableThread.__init__(self)
    self.flickr   = flickr
    self.callback = callback
    self.start()
    
  def run(self):
    try:
      self.flickr.load_photosets(self.callback)
      #Publisher().sendMessage(('UpdateFlickrTree'), None)
    except wx.PyDeadObjectError:
      # thread is stopped
      pass
      
class DownloadPhotosetsThread(StoppableThread):
  def __init__(self, flickrPhotosets, callback = None):
    '''
    callback(flickr.Photoset, flickr.Photo, progress, done)
    '''
    StoppableThread.__init__(self)
    
    self.flickrPhotosets  = flickrPhotosets
    self.callback         = callback
    self.start()
    
  def run(self):
    try:
      for flickrPhotoset in self.flickrPhotosets:
        flickrPhotoset.download(callback)
    except wx.PyDeadObjectError:
      pass