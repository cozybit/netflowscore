import os
import urllib
import webapp2
import random
import uuid 
import logging
import bisect

from datetime import datetime, timedelta
from google.appengine.ext import ndb

TEST_ITERATIONS = 10

SCORING = [
    ( 1100, 'EXCELLENT' ),
    ( 1400, 'GOOD' ),
    ( 2000, 'FAIR' ),
    ( 2500, 'POOR' ),
]

class TestPoint(ndb.Model):
    model = ndb.StringProperty()
    user_agent = ndb.StringProperty()
    start_times = ndb.DateTimeProperty(repeated=True)
    end_times = ndb.DateTimeProperty(repeated=True)
    iteration = ndb.IntegerProperty()
    score = ndb.IntegerProperty()

class StartHandler(webapp2.RequestHandler):
  def get(self):
    model = self.request.get('model')
    user_agent = str(self.request.headers['User-Agent'])
    logging.info("model=" + model)
    token = str(uuid.uuid4())
    self.response.set_status(303)
    self.response.headers['Location'] = '/test?token=' + token
    tp = TestPoint(id=token)
    tp.start_times = []
    tp.end_times = []
    tp.iteration = TEST_ITERATIONS
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

    # All requests redirected to this handler, except for the last iteration
    # that goes to the result page. 
    self.response.set_status(303)

    # start times recorded in all iterations but last
    # end times recorded in all iterations but first
    if tp.iteration != 0:
      tp.start_times.append(datetime.now())
      self.response.headers['Location'] = '/test?token=' + token
    else:
      self.response.headers['Location'] = '/result?token=' + token

    if tp.iteration != TEST_ITERATIONS:
      tp.end_times.append(datetime.now())

    tp.iteration -= 1;
    tp.put()

class ResultHandler(webapp2.RequestHandler):
  def get(self):
    token = self.request.get('token')
    tp = TestPoint.get_by_id(token)

    if not tp:
      logging.error("Test is not in progress.")

    measurements = zip(tp.start_times, tp.end_times)
    deltas = [m[1] - m[0] for m in measurements]
    avg_delta = sum(deltas, timedelta(0)) / len(deltas)
    avg_delta_in_msecs = int(1000 * avg_delta.total_seconds())
    
    logging.info("measurement = " + str(avg_delta_in_msecs))

    score_idx = bisect.bisect_right(SCORING, (avg_delta_in_msecs, ))
    logging.info("score = " + SCORING[score_idx][1])

    self.response.headers['Content-Type'] = 'text/plain'
    self.response.out.write(SCORING[score_idx][1])

class MainHandler(webapp2.RequestHandler):
  def get(self):
    self.response.out.write(random.getrandbits(1000))

application = webapp2.WSGIApplication([('/', MainHandler),
                              ('/start', StartHandler),
                              ('/test', TestHandler),
                              ('/result', ResultHandler)],
                              debug=True)
