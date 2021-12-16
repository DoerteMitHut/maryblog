import sys
import random
from flask import Flask, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func

import overpy
import what3words
import os
import requests
import json

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'

db = SQLAlchemy(app)
geocoder = what3words.Geocoder("15V3XXO6")

BASECOORDS = [52.396947, 12.944850]


# class PostTemplate(db.Model):
#     id = db.Column(db.Integer,primary_key=True)
#     template_name = db.Column(db.String(27),nullable=False)
#     template_file = db.Column(db.String(32),nullable=False)

#     def __init__(self,id,name,filename=""):
#         self.id = id
#         self.template_name = name
#         if template_file == "":
#             self.template_file = ".".join([template_name,"html"])
#         else:
#             self.template_file = template_file



class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    template = db.Column(db.String(20),nullable = False)
    #template_id = db.Column(db.Integer, db.ForeignKey('post_template.id'))
    #template = db.relationship("PostTemplate")

    author = db.Column(db.String(20),nullable = False)

    creation_timestamp = db.Column(db.DateTime,nullable=False)
    headline = db.Column(db.String(100),nullable=False,unique=True)
    summary = db.Column(db.String(300),nullable=True)
    content_file = db.Column(db.String(50),nullable=False)
    def __init__(self, id, template, author, creation_timestamp, headline, summary, content_file):
        self.id = id
        self.template = template
        self.author = author
        self.creation_timestamp = creation_timestamp
        self.headline = headline
        self.summary = summary
        self.content_file = content_file

    def __repr__(self):
        return "<Post Nr.%d | %s | created <%s> by %s" % (self.id, self.headline, self.creation_timestamp, self.author)

class Point(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    latitude_off = db.Column(db.Float)
    longitude_off = db.Column(db.Float)
    district_id = db.Column(db.Integer, db.ForeignKey('district.id'))
    district = db.relationship("District")

    def __init__(self, id, district, lat, lng):
        self.id = id
        self.district = district
        self.latitude_off = lat
        self.longitude_off = lng

    def __repr__(self):
        return "<Point %d: Lat %s Lng %s>" % (self.id, self.latitude_off, self.longitude_off)

    @property
    def latitude(self):
        return self.latitude_off + self.district.latitude

    @property
    def longitude(self):
        return self.longitude_off + self.district.longitude


class District(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)

    def __init__(self, id, name, lat, lng):
        self.id = id
        self.name = name
        self.latitude = lat
        self.longitude = lng




@app.route('/')
@app.route('/index')
def index():
    districts = District.query.all()

    posts = Post.query.all()

    return render_template('index.html', districts=districts,twa=geocoder.convert_to_3wa(what3words.Coordinates(52.417429,12.917370),language='de'),posts=posts)

@app.route('/about')
def about():
    districts = District.query.all()
    return render_template('about.html', districts=districts)

@app.route('/contact')
def contact():
    districts = District.query.all()
    return render_template('contact.html', districts=districts)

@app.route('/post')
def post():
    return render_template('post.html', post=Post.query.all()[0])

@app.route('/post/<int:post_id>')
def singlepost(post_id):
    return render_template('post.html', post=Post.query.filter_by(id=post_id).all()[0])

@app.route('/district/<int:district_id>')
def district(district_id):
    points = Point.query.filter_by(district_id=district_id).all()
    coords = [[point.latitude, point.longitude] for point in points]
    return jsonify({"data": coords})

@app.route('/gallery')
def gallery():
    return render_template('gallery.html')

@app.route('/todo')
def todo():
    todocards = json.loads(requests.get('https://api.trello.com/1/lists/5f6899f8602a436d5c316547/cards?key=cb9a3197e4b1cedd7d3a7f31e6735bb6&token=84565059fbc2fecf5ecc6260c24a10d3d1da1d2ca5bcc004f7d2336c7aced49f').text)
    donecards = json.loads(requests.get('https://api.trello.com/1/lists/61977c2bdfd08d75122dbb06/cards?key=cb9a3197e4b1cedd7d3a7f31e6735bb6&token=84565059fbc2fecf5ecc6260c24a10d3d1da1d2ca5bcc004f7d2336c7aced49f').text)
    cards = todocards + donecards
    return render_template('todo.html',donecards=donecards,todocards=todocards)

@app.route('/todotest')
def todotest():
    todocards = json.loads(requests.get('https://api.trello.com/1/lists/5f6899f8602a436d5c316547/cards?key=cb9a3197e4b1cedd7d3a7f31e6735bb6&token=84565059fbc2fecf5ecc6260c24a10d3d1da1d2ca5bcc004f7d2336c7aced49f').text)
    donecards = json.loads(requests.get('https://api.trello.com/1/lists/61977c2bdfd08d75122dbb06/cards?key=cb9a3197e4b1cedd7d3a7f31e6735bb6&token=84565059fbc2fecf5ecc6260c24a10d3d1da1d2ca5bcc004f7d2336c7aced49f').text)
    cards = todocards + donecards
    return render_template('todotest.html',donecards=donecards,todocards=todocards)


def make_random_data(db):
    db.session.query(Point).delete()
    db.session.query(District).delete()
    db.session.commit()
    NDISTRICTS = 5
    NPOINTS = 10
    for did in range(NDISTRICTS):
        district = District(did, "District %d" % did, BASECOORDS[0], BASECOORDS[1])
        db.session.add(district)
        for pid in range(NPOINTS):
            lat = random.random() - 0.5
            lng = random.random() - 0.5
            row = Point(pid + NPOINTS * did, district, lat, lng)
            db.session.add(row)
    db.session.commit()

def make_random_data(db):
    def bbox(lat,long,rad = 0.1):
        return f"({lat-rad},{long-rad},{lat+rad},{long+rad})"

    api = overpy.Overpass()

    q = f'node[\"highway\"=\"bus_stop\"]{bbox(BASECOORDS[0], BASECOORDS[1],0.05)};out;'
    print(q)
    result = api.query(q)
    print(len(result.nodes))
    

    db.session.query(Point).delete()
    db.session.query(District).delete()
    db.session.commit()
    NDISTRICTS = 1
    for did in range(NDISTRICTS):
        district = District(did, "District %d" % did, BASECOORDS[0], BASECOORDS[1])
        db.session.add(district)
        for pid,n in enumerate(result.nodes):
            print(n.tags['name'])
            lat = float(n.lat)-BASECOORDS[0]
            lng = float(n.lon)-BASECOORDS[1]
            row = Point(pid, district, lat, lng)
            db.session.add(row)
    db.session.commit()

def readPosts(db):
    db.session.query(Post).delete()
    HEADLINES = ["Bester Post", "Post 2", "Do Androids dream of Electric Sheep?", "A Fish in the Ocean"]
    SUMMARIES = ["Der beste Post wo gibt", "Ein Sequel zum Besten Post wo gibt. Kann ja nur schlimmer werden.", "Like..., I mean... DO THEY?!", ".. is pretty fuckoed up but still better off than one on land."]
    CONTENTS = ["42 ist die Antwort", "43 ist nichts", "zzzzzZZZZZZzzzzzZZZZ baaaa!", "Blub! Blub!"]
    for i,f in enumerate(os.listdir('templates/posts')):
        if not f.startswith('.'):
            fo = open(f"templates/posts/{f}")
            s = fo.read()
            p = Post(i,"None","Niklas",func.now(),f.split('.')[0].replace('_', ' '),s.split('=ENDSUMMARY=')[0],f)
            fo.close()
            db.session.add(p)
    db.session.commit()


if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == 'mkdb':
            db.create_all()
            make_random_data(db)
            readPosts(db)
    else:
        app.run(debug=True)
