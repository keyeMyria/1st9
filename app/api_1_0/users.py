# encoding: utf-8
from flask import jsonify, request, current_app, url_for
from . import api
from ..models import User, Mp
from flask_jwt import jwt_required, current_identity
from flask_security import auth_token_required
from .. import db

@api.route('/protected2')
@jwt_required()
def protected2():
    return 'this is JWT protected, user_id: %s' % current_identity

@api.route('/protected')
@auth_token_required
def token_protected():
	return 'you\'re logged in by Token!'

"""
# not use below API, only use built-in Flask-Security register
@api.route('/register', methods=['GET', 'POST'])
def register():
    username = request.get_json()['username']
    password = request.get_json()['password']
    print 'register Header: %s\nusername: %s, password:%s'% (request.headers, username, password)
    if username <> '' and password <> '':
        if User.query.filter_by(email=username).first():
             return jsonify({
            'status': 'failure',
            'msg': u'用户名已被占用，换一个吧'
            })           

        user = User(email=username, password=password)
        db.session.add(user)
        db.session.commit()
        return jsonify({
        'status': 'success',
        'msg': 'register OK, please login!'
        })
    return jsonify({
    'status': 'failure',
    'msg': 'register fail, check username and password.'
    })
"""

@api.route('/users/<int:id>')
@auth_token_required
def get_user(id):
    user = User.query.get_or_404(id)
    return jsonify(user.to_json())


@api.route('/users/<int:id>/posts/')
def get_user_posts(id):
    user = User.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    pagination = user.posts.order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    posts = pagination.items
    prev = None
    if pagination.has_prev:
        prev = url_for('api.get_user_posts', page=page-1, _external=True)
    next = None
    if pagination.has_next:
        next = url_for('api.get_user_posts', page=page+1, _external=True)
    return jsonify({
        'posts': [post.to_json() for post in posts],
        'prev': prev,
        'next': next,
        'count': pagination.total
    })


@api.route('/users/<int:id>/timeline/')
def get_user_followed_posts(id):
    user = User.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    pagination = user.followed_posts.order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    posts = pagination.items
    prev = None
    if pagination.has_prev:
        prev = url_for('api.get_user_followed_posts', page=page-1,
                       _external=True)
    next = None
    if pagination.has_next:
        next = url_for('api.get_user_followed_posts', page=page+1,
                       _external=True)
    return jsonify({
        'posts': [post.to_json() for post in posts],
        'prev': prev,
        'next': next,
        'count': pagination.total
    })
