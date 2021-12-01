import sys
import random
from flask import Flask, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
import overpy
import what3words

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'

db = SQLAlchemy(app)
geocoder = what3words.Geocoder("15V3XXO6")

BASECOORDS = [52.396947, 12.944850]


class PostTemplate(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    template_name = db.Column(db.String(27),nullable=False)
    template_file = db.Column(db.String(32),nullable=False)

    def __init__(self,id,name,filename=""):
        self.id = id
        self.template_name = name
        if template_file == "":
            self.template_file = ".".join([template_name,"html"])
        else:
            self.template_file = template_file



class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    template_id = db.Column(db.Integer, db.ForeignKey('post_template.id'))
    template = db.relationship("PostTemplate")

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
    return render_template('index.html', districts=districts,twa=geocoder.convert_to_3wa(what3words.Coordinates(52.417429,12.917370),language='de'))

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
    return render_template('post.html', districts=districts)

@app.route('/district/<int:district_id>')
def district(district_id):
    points = Point.query.filter_by(district_id=district_id).all()
    coords = [[point.latitude, point.longitude] for point in points]
    return jsonify({"data": coords})


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


if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == 'mkdb':
            db.create_all()
            make_random_data(db)
    else:
        app.run(debug=True)
