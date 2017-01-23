# encoding: utf-8
from flask import jsonify, request, g, abort, url_for, current_app
from .. import db
from ..models import Mp, User
from . import api
from flask_security import auth_token_required


@api.route('/mps', methods=['POST'])
@auth_token_required
def new_mps():
    email = request.get_json()['email']
    user = User.query.filter_by(email=email).first()
    Mps = Mp.from_json(request.json)
#    subscribed_mps = user.subscribed_mps
    subscribed_mps_weixinhao = [i.weixinhao for i in user.subscribed_mps]
    rsp = []
    for mp in Mps:
	    mp_sql = Mp.query.filter_by(weixinhao=mp.weixinhao).first()
#	    print mp.weixinhao,  mp.weixinhao in subscribed_mps_weixinhao
	# 如果不存在这个订阅号，则添加到Mp，并订阅
	    if mp_sql is None:
	    		db.session.add(mp)
	    		user.subscribe(mp)
	    		rsp.append(mp.to_json())
	    		db.session.commit()
	# 如果用户没有订阅，则订阅
	    elif not mp.weixinhao in subscribed_mps_weixinhao:
	    		user.subscribe(mp_sql)
	    		rsp.append(mp.to_json())
	    		db.session.commit()
     # TODO: 删除不再订阅的公众号

            
    return jsonify(rsp), 201, \
        {'Location': url_for('api.get_mps', id=mp.id, _external=True)}


# 带 /mps/ 斜杠的，必须放在 /mps POST后面，不然默认会选择以下GET
@api.route('/mps/')
@auth_token_required
def get_mps():
	# request.args.items().__str__()
	email = request.args.get('email')
	print email
	mps = User.query.filter_by(email=email).first().subscribed_mps
	mps_list = [ mp.to_json() for mp in mps ]
	print mps_list
	return jsonify(mps_list)
