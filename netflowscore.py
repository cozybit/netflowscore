import os
import urllib
import webapp2
import random
import uuid 
import logging
import bisect

from datetime import datetime, timedelta
from google.appengine.ext import ndb

TEST_DEADLINE_IN_SECS = 10.0  

def create_test_point(netnode_idx, calibration = False):
    token = str(uuid.uuid4())
    tp = TestPoint(id=token)
    tp.iteration = 0
    tp.freeze_size_iteration = 0
    tp.calibration = calibration 
    tp.netnode_idx = netnode_idx
    tp.put()
    return token

# indexed by ip_addr + device_type OR, by ip_addr alone, if device type not
# available 
class NetworkNodeModel(ndb.Model):
    reference_score = ndb.IntegerProperty()
    ip_addr = ndb.StringProperty()
    device_type = ndb.StringProperty()

class TestPoint(ndb.Model):
    calibration = ndb.BooleanProperty()
    netnode_idx = ndb.StringProperty()
    start_time = ndb.DateTimeProperty(auto_now_add=True)
    iteration = ndb.IntegerProperty()
    freeze_size_iteration = ndb.IntegerProperty()
    score = ndb.IntegerProperty()

class StartHandler(webapp2.RequestHandler):
  def get(self):
    ip = self.request.remote_addr
    device_type = self.request.get('device_type')

    netnode_idx = ip + device_type

    nn = NetworkNodeModel.get_by_id(netnode_idx)
    if nn == None:
      self.error(403)
      self.status_message = "This device is not calibrated on this network. /calibrate first."
      return

    logging.info("Starting test for device idx: " + netnode_idx)
    token = create_test_point(netnode_idx)
    self.response.set_status(303)
    self.response.headers['Location'] = '/test?token=' + token

class CalibrateHandler(webapp2.RequestHandler):
  def get(self):
    ip = self.request.remote_addr
    device_type = self.request.get('device_type')

    netnode_idx = ip + device_type

    # look up or create the NetworkNode
    nn = NetworkNodeModel.get_by_id(netnode_idx)
    if nn == None:
      logging.info("Created new network node with id: " + netnode_idx)
      nn = NetworkNodeModel(id=netnode_idx)
      nn.device_type = device_type
      nn.put()
    else:
      logging.info("Recalibrated network node with id: " + netnode_idx)
    
    # launch a test with calibration flag
    token = create_test_point(netnode_idx, calibration=True)
    self.response.set_status(303)
    self.response.headers['Location'] = '/test?token=' + token

class TestHandler(webapp2.RequestHandler):
  def get(self):
    token = str(self.request.get('token'))
    tp = TestPoint.get_by_id(token)
    if not tp:
      self.error(500)
      self.status_message = "Test is not in progress."
      logging.error("Test is not in progress.")


    # All requests redirected to this handler, except for the last iteration
    # that goes to the result page. 
    self.response.set_status(303)

    delta = datetime.now() - tp.start_time
    if (delta.total_seconds() > TEST_DEADLINE_IN_SECS):
      self.response.headers['Location'] = '/result?token=' + token
    else:
      self.response.headers['Location'] = '/test?token=' + token
      for i in range(1000 * (1 << tp.freeze_size_iteration)):
        self.response.out.write("%04x" % i)

    tp.iteration += 1;
    if (delta.total_seconds() < TEST_DEADLINE_IN_SECS / 4):
      tp.freeze_size_iteration += 1
    tp.put()

class ResultHandler(webapp2.RequestHandler):
  def get(self):
    token = self.request.get('token')
    tp = TestPoint.get_by_id(token)

    if not tp:
      logging.error("Test is not in progress.")

    # try to look up the NetworkNode
    nn = NetworkNodeModel.get_by_id(tp.netnode_idx)

    if nn == None:
      logging.error("Could not find network node for calibration test for idx "
         + tp.netnode_idx)
      return

    if tp.calibration:
      nn.reference_score = tp.iteration
      tp.calibration = False
      nn.put()

    score = float(min(tp.iteration, nn.reference_score)) / nn.reference_score
    logging.info("score = %.2f" % score)

    self.response.headers['Content-Type'] = 'text/plain'
    self.response.out.write("%.2f" % score)

class MainHandler(webapp2.RequestHandler):
  def get(self):
    self.response.out.write(random.getrandbits(1000))

application = webapp2.WSGIApplication([('/', MainHandler),
                              ('/start', StartHandler),
                              ('/test', TestHandler),
                              ('/result', ResultHandler),
                              ('/calibrate', CalibrateHandler)],
                              debug=True)
