import flickrapi

handle  = None
token   = None
key     = '33726ac0a25ecf1ef45f889008fbf457'
secret  = '58cc6410cf7a4883'
frob    = None
nsid    = None

# authentication ==============================================================

def login():
  global handle, token, secret, frob, nsid
  
  auth_url  = None
  
  if not token:
    handle  = flickrapi.FlickrAPI(key, secret)
    (token, frob, nsid, auth_url) = handle.get_token_part_one(perms = 'write')

    if token:
      handle  = flickrapi.FlickrAPI(key, secret, nsid, token)
      
      return (True, None)
      
  return (False, auth_url)
  
def auth():
  global handle, token, frob, nsid
  
  (token, nsid) = handle.get_token_part_two((token, frob))

# photo =======================================================================

def upload_photo(path, title, callback = None):
  global handle
  
  rsp       = handle.upload(path.encode('utf-8'), title = title, is_public = 0, callback = callback)
  photo_id  = rsp.find('photoid').text
  
  return photo_id
  
def photo_url(photo_id, label = 'Original'):
  global handle, key
  
  rsp = handle.photos_getSizes(api_key = key, photo_id = photo_id)
  for size in rsp.find('sizes').findall('size'):
    if size.attrib['label'] == label:
      return size.attrib['source']
      
  return None
  
# photoset ====================================================================
  
def find_photoset_ids(title):
  global handle, key, nsid
  
  photoset_ids  = []
  
  rsp = handle.photosets_getList(api_key = key, user_id = nsid)
  for photoset in rsp.find('photosets').findall('photoset'):
    if photoset.find('title').text == title:
      photoset_ids.append(photoset.attrib['id'])
      
  return photoset_ids
  
def load_photosets():
  global handle, key, nsid
  
  photosets = []
  
  rsp = handle.photosets_getList(api_key = key, user_id = nsid)
  
  for photoset in rsp.find('photosets').findall('photoset'):    
    photosets.append(dict(id = photoset.attrib['id'], primary = photoset.attrib['primary'], title = photoset.find('title').text, description = photoset.find('description').text))
    
  return photosets
  
def load_photos(photoset_id):
  global handle, key
  
  page    = 1
  pages   = 0
  photos  = []

  while True:
    rsp = handle.photosets_getPhotos(api_key = key, photoset_id = photoset_id, page = page)
    
    for photoset in rsp.findall('photoset'):
      if pages == 0:
        pages = int(photoset.attrib['pages']) # save total number of pages

      for photo in photoset.findall('photo'):
        photos.append(dict(id = photo.attrib['id'], title = photo.attrib['title']))

    if page == pages:
      break

    page  += 1  # check next page
    
  return photos
  
def create_photoset(title, description, photo_id):
  global handle, key
  
  rsp = handle.photosets_create(api_key = key, title = title, description = description, primary_photo_id = photo_id)
  photoset_id = rsp.find('photoset').attrib['id']
    
  return photoset_id
  
def add_photo(photoset_id, photo_id):
  global handle, key
  
  handle.photosets_addPhoto(api_key = key, photoset_id = photoset_id, photo_id = photo_id)