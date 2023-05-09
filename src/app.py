from flask import (
	Flask, 
	jsonify, 
	request, 
	session 
)
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql.expression import func
import itertools

app = Flask(__name__)
app.config.from_mapping(
	SECRET_KEY='your secret here', 
	SQLALCHEMY_DATABASE_URI='sqlite:///example.db'
)
CORS(app)
db = SQLAlchemy(app)

QUESTS = [
	{
		"question": "The first video game is known as …",
		"answers": [
			"Pong",
			"OXO",
			"Pac-Man",
			"Space Invaders"
		],
		"answer": 2
	},
	{
		"question": "How many bits does a nibble have?",
		"answers": [
			2,
			8,
			16, 
			64
		],
		"answer": 3
	},
	{
		"question": "Urban Müller created a programming language in 1993 called …",
		"answers": [
			"Haskell",
			"Lua",
			"Brainfuck",
			"Prolog"
		],
		"answer": 3
	},
	{
		"question": "Which proccessor have the option of operating in either little-endian or big-endian mode?",
		"answers": [
			"x86",
			"SPARC",
			"PowerPC",
			"ARM"
		],
		"answer": 4
	},
	{
		"question": "When did the first iPhone come out?",
		"answers": [
			2000,
			2002,
			2005,
			2007
		],
		"answer": 4
	}, 
	{
		"question": "What do you think?",
		"answers": [
			"Ok",
			"Easy",
			"Hmmm",
			"Not bad"
		],
		"answer": 3
	}, 
	{
		"level": 2, 
		"question": "Who had a hit with 'St. Elmo's Fire (Man In Motion)' in 1985?", 
		"answers": [
			"The S.O.S. Band", 
			"John Parr", 
			"Neil Diamond", 
			"New Kids On The Block" 
		], 
		"answer": 2
	}, 
	{
		"level": 2, 
		"question": "What year did MC Hammer release his song 'U Can't Touch This'?", 
		"answers": [
			1989, 
			1992, 
			1990, 
			1986 
		], 
		"answer": 3
	}, 
]

class Quest(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	level = db.Column(db.Integer, nullable=0, default=1)
	question = db.Column(db.String, unique=True)
	answers = db.Column(db.JSON, nullable=False)
	answer = db.Column(db.Integer, nullable=False)


with app.app_context():
	db.drop_all()
	db.create_all()

	qs = [Quest(**quest) for quest in QUESTS]
	db.session.add_all(qs)
	db.session.commit()

@app.route('/quest')
def quest():
	lvl = session['level'] = 1
	pts = session['score'] = 0

	# q = Quest.query.filter_by(level=lvl).order_by(func.random()).first_or_404()
	q = db.first_or_404(db.select(Quest).filter(Quest.level==lvl).order_by(func.random()))
	session['qid'] = q.id
	session['qids'] = []
	session['fails'] = 0

	return jsonify(
		level=lvl, 
		score=pts, 
		question=q.question, 
		answers=q.answers, 
		finished=False
	)

@app.post('/quest')
def quest_solve():
	lvl = session.get('level', 1)
	pts = session.get('score', 0) 
	qid = session.get('qid')
	
	# q = Quest.query.get_or_404(qid)
	q = db.get_or_404(Quest, qid)

	if int(request.json.get('value', 0)) == q.answer: 
		session['qids'].append(q.id)
		pts = session['score'] = (pts + 10) 
		if pts >= lvl*50:
			lvl = session['level'] = lvl + 1
			session['qids'] = []
			# if lvl > db.session.query(func.max(Quest.level)).scalar():
			if lvl > db.session.execute(db.select(func.max(Quest.level))).scalar():
				lvl = session['level'] = 1
	else:
		session['fails'] += 1 

	# qs = Quest.query.filter(Quest.level==lvl, Quest.id.not_in(session['qids'] + [q.id])).order_by(func.random()).first()
	stmt = db\
		.select(Quest)\
		.where(Quest.level==lvl, Quest.id.not_in(session['qids'] + [q.id]))\
		.order_by(func.random())\
		.limit(1)
	qs = db.session.execute(stmt).scalar()
	if qs: q = qs
	done = session['fails'] >= 3 or q.id in session['qids'] # q is None
	session['qid'] = q.id if q else 0

	return jsonify(
		level=lvl, 
		score=pts, 
		question= q.question if q else None, 
		answers= q.answers if q else None, 
		finished=done
	)

