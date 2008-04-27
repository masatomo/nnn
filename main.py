#!/usr/bin/env python

import wsgiref.handlers
import datetime
import cgi

from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.ext import webapp

class Pic(db.Model):
  name = db.StringProperty()
  content = db.BlobProperty()
  author = db.UserProperty()
  updated = db.DateTimeProperty(auto_now_add=True)
  created = db.DateTimeProperty(auto_now_add=True)

class PicComment(db.Model):
  pic = db.ReferenceProperty(Pic)
  comment = db.StringProperty()
  author = db.UserProperty()
  updated = db.DateTimeProperty(auto_now_add=True)
  created = db.DateTimeProperty(auto_now_add=True)

class MainPage(webapp.RequestHandler):
  def get(self):
    user = users.get_current_user()
    if user:
      greeting = ("Welcome, %s! (<a href=\"%s\">sign out)" %
                  (user.nickname(), users.create_logout_url("/")))
    else:
      greeting = ("<a href=\"%s\">Sign in</a>(Optional)" %
                  users.create_login_url("/"))

    self.response.out.write('<html><head><meta http-equiv="Content-Type" content="text/html; charset=utf-8"></head>')
    self.response.out.write('<html>')
    self.response.out.write('<body>')

    self.response.out.write('Code: <a href="http://freehg.org/u/masatomo/nnn/">http://freehg.org/u/masatomo/nnn/</a>')
    self.response.out.write("<hr>")

    self.response.out.write("<h2>%s</h2>" % greeting)

    self.response.out.write("<hr>")

    for pic in db.GqlQuery("SELECT * FROM Pic Order by updated desc limit 10"):
      self.response.out.write('<a name="' + str(pic.key()) + '"></a>')
      self.response.out.write('<img border="1" src="/ShowPic/' + str(pic.key()) + '">')

      self.response.out.write('<ul>')
      for picComment in db.GqlQuery("SELECT * FROM PicComment WHERE pic=:thispic Order by updated", thispic=pic):
        if (picComment.author):
          name = picComment.author.nickname()
        else:
          name = 'nanashi'
        self.response.out.write('<li>' + cgi.escape(name) + ' : ' + cgi.escape(picComment.comment) + '</li>')
      self.response.out.write('<li>')
      self.response.out.write("""
        <form action="/AddComment/""" + str(pic.key()) + """" method="post">
        <input type="text" size="50" name="comment">
        <input type="submit" value="Add">
        </form>
      """)
      self.response.out.write('</li>')
      self.response.out.write('</ul>')
      self.response.out.write('<hr>')

    self.response.out.write("""
      <form action="/UploadPic" enctype='multipart/form-data' method="post">
      <table>
      <tr><td>Upload File:</td><td><input type="file" name="content"></td></tr>
      <tr><td>Comment:</td><td><input type="text" size="50" name="comment"></td>
      <tr><td><input type="submit" value="Upload"></td></tr>
      </table>
      </form>""")

    self.response.out.write("</body></html>")
    
class ShowPic(webapp.RequestHandler):
  def get(self, picKey):
    try:
      key = db.Key(picKey)
    except db.BadKeyError:
      self.response.out.write("Broken Key")
      return

    pic = db.GqlQuery("SELECT * FROM Pic Where ANCESTOR IS :key", key=db.Key(picKey)).get()
    if pic:
      #self.response.headers["Content-Type"] = "image/jpeg"
      self.response.out.write(pic.content)
    else:
      self.response.out.write("NOT FOUND")

class AddComment(webapp.RequestHandler):
  def post(self, picKey):
    try:
      key = db.Key(picKey)
    except db.BadKeyError:
      self.response.out.write("Broken Key")
      return
    pic = db.GqlQuery("SELECT * FROM Pic Where ANCESTOR IS :key", key=db.Key(picKey)).get()
    if pic:
      picComment = PicComment()
      picComment.pic = pic
      picComment.comment = self.request.get('comment')
      if users.get_current_user():
        picComment.author = users.get_current_user()
      picComment.put()

    self.redirect("/#" + str(pic.key()))

class UploadPic(webapp.RequestHandler):
  def post(self):
    uploaded = self.request.get('content')

    if (len(uploaded) > 1024*1024):
      self.response.out.write("Maximum File size: 1MB")
      return

    pic = Pic()
    pic.content = self.request.get('content')
    if users.get_current_user():
      pic.author = users.get_current_user()
    pic.put()

    if (self.request.get('comment')):
      picComment = PicComment()
      picComment.pic = pic
      picComment.comment = self.request.get('comment')
      if users.get_current_user():
        picComment.author = users.get_current_user()
      picComment.put()

    self.redirect("/")



def main():
  application = webapp.WSGIApplication([
      ('/', MainPage),
      (r'/ShowPic/([a-zA-Z0-9]+)', ShowPic),
      ('/UploadPic', UploadPic),
      (r'/AddComment/([a-zA-Z0-9]+)', AddComment),
],debug=True)
  wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
  main()
