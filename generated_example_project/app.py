from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
db = SQLAlchemy(app)

class Entry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    
    def __repr__(self):
        return f'<Entry {self.title}>'

db.create_all()

@app.route('/')
def index():
    entries = Entry.query.order_by(Entry.id.desc()).all()
    return render_template('index.html', entries=entries)

if __name__ == '__main__':
    app.run(debug=True)
