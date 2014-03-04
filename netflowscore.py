import os
import urllib
import webapp2
import random
import uuid 
import logging
from datetime import datetime

from google.appengine.ext import ndb

class TestPoint(ndb.Model):
    model = ndb.StringProperty()
    start_time = ndb.DateTimeProperty(auto_now_add=True)
    end_time = ndb.DateTimeProperty()
    score = ndb.IntegerProperty()

class StartHandler(webapp2.RequestHandler):
  def get(self):
    model = self.request.get('model')
    if not model:
      # if not given explicitely, get it from browser
      model = str(self.request.headers['User-Agent'])
    logging.info("model=" + model)
    token = str(uuid.uuid4())
    self.response.set_status(303)
    self.response.headers['Location'] = '/test?token=' + token
    tp = TestPoint(id=token)
    tp.end_time = datetime.max
    tp.put()

class TestHandler(webapp2.RequestHandler):
  def get(self):
    token = str(self.request.get('token'))
    tp = TestPoint.get_by_id(token)
    if not tp:
      self.error(500)
      self.status_message = "Test is not in progress."
      logging.error("Test is not in progress.")
    for i in range(100000):
      self.response.out.write("%04x" % i)
    self.response.set_status(303)
    self.response.headers['Location'] = '/result?token=' + token

class ResultHandler(webapp2.RequestHandler):
  def get(self):
    token = self.request.get('token')
    tp = TestPoint.get_by_id(token)

    if not tp:
      logging.error("Test is not in progress.")

    if tp.end_time == datetime.max:
      tp.end_time = datetime.now()
      tp.put()

    delta = tp.end_time - tp.start_time
    logging.info("delta:" + str(delta.microseconds) + " end_time:" + str(tp.end_time))
    self.response.out.write("score =" + str(delta.total_seconds()))
    self.response.out.write('<div><a href="/start">retest</a></div>')

class MainHandler(webapp2.RequestHandler):
  def get(self):
    self.response.out.write(random.getrandbits(1000))

application = webapp2.WSGIApplication([('/', MainHandler),
                              ('/start', StartHandler),
                              ('/test', TestHandler),
                              ('/result', ResultHandler)],
                              debug=True)
