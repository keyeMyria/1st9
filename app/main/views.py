# encoding: utf-8
from flask import render_template, redirect, url_for, abort, flash, request,\
    current_app, make_response, jsonify
from flask_security import Security, SQLAlchemyUserDatastore, current_user, AnonymousUser, \
    UserMixin, RoleMixin, login_required, auth_token_required, http_auth_required
from flask_security.utils import logout_user
from flask_sqlalchemy import get_debug_queries
from . import main
#from .forms import EditProfileForm, EditProfileAdminForm, PostForm, CommentForm
from .. import db, admin
from flask_admin import Admin, BaseView, expose
from flask_admin.contrib.sqla import ModelView
from flask_admin._backwards import ObsoleteAttr
from ..models import User, Mp, Article, Role, Subscription,  roles_users
#from ..decorators import admin_required, permission_required
from flask_admin import helpers as admin_helpers

# 后台管理页面的首页
class MyView(BaseView):
    @expose('/')
    def index(self):
        return self.render('admin/index.html')

# Create customized model view class
class MyModelViewBase(ModelView):
	# 字段（列）格式化
	# `view` is current administrative view
    # `context` is instance of jinja2.runtime.Context
    # `model` is model instance
    # `name` is property name
    column_display_pk = True # optional, but I like to see the IDs in the list
#    column_list = ('id', 'name', 'parent')
    column_auto_select_related = ObsoleteAttr('column_auto_select_related',
                                              'auto_select_related',
                                              True)
    column_display_all_relations = True


    def is_accessible(self):
        if not current_user.is_active or not current_user.is_authenticated:
            return False
        if current_user.has_role('superuser'):
            return True
        return False
        
    def _handle_view(self, name, **kwargs):
        """
        Override builtin _handle_view in order to redirect users when a view is not accessible.
        """
        if not self.is_accessible():
            if current_user.is_authenticated:
                # permission denied
                abort(403)
            else:
                # login
                return redirect(url_for('security.login', next=request.url))

class MyModelViewUser(MyModelViewBase):
    #column_select_related_list = ['mps',]
    # TODO: models.User.mps 加了 dynamic, 则Flask-Admin里显示raw-SQL；不加，则models里的methods出错！
	column_formatters = dict(
		password=lambda v, c, m, p: '**'+m.password[-6:],
		mps=lambda v, c, m, p: (m.subscribed_mps_str),	# '\n\p'.join
		)
	column_searchable_list = (User.email, )
    
class MyModelViewMp(MyModelViewBase):
    #column_select_related_list = ['subscribers',]
	column_formatters = dict(
		subscribers=lambda v, c, m, p: (m.subscribers_str),	# '\n\p'.join
		articles=lambda v, c, m, p: (m.articles_str),
		)
	column_searchable_list = (Mp.weixinhao, Mp.mpName, )

# Role/User管理页面，需要Login
admin.add_view(MyModelViewBase(Role, db.session))
admin.add_view(MyModelViewUser(User, db.session))
admin.add_view(MyModelViewMp(Mp, db.session))
admin.add_view(MyModelViewBase(Subscription, db.session))
admin.add_view(MyModelViewBase(Article, db.session))

@main.route('/', methods=['GET', 'POST'])
def index():
#    return 'hello'
	return render_template('index.html')

@main.route('/__webpack_hmr')
def npm():
    return redirect('http://localhost:8080/__webpack_hmr')

@main.route('/protected')
@login_required
def protected():
	print current_user.to_json()
	print ', '.join(['%s:%s' % item for item in current_user.__dict__.items()])
	if current_user <> AnonymousUser and not current_user.is_active:
		logout_user()
		return "you've been logged out!"	
	return "protected view!"

@main.route('/user/<username>')
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    pagination = user.posts.order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    posts = pagination.items
    return render_template('user.html', user=user, posts=posts,
                           pagination=pagination)


@main.route('/post/<int:id>', methods=['GET', 'POST'])
def post(id):
    post = Post.query.get_or_404(id)
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(body=form.body.data,
                          post=post,
                          author=current_user._get_current_object())
        db.session.add(comment)
        flash('Your comment has been published.')
        return redirect(url_for('.post', id=post.id, page=-1))
    page = request.args.get('page', 1, type=int)
    if page == -1:
        page = (post.comments.count() - 1) // \
            current_app.config['FLASKY_COMMENTS_PER_PAGE'] + 1
    pagination = post.comments.order_by(Comment.timestamp.asc()).paginate(
        page, per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],
        error_out=False)
    comments = pagination.items
    return render_template('post.html', posts=[post], form=form,
                           comments=comments, pagination=pagination)


@main.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    post = Post.query.get_or_404(id)
    if current_user != post.author and \
            not current_user.can(Permission.ADMINISTER):
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.body = form.body.data
        db.session.add(post)
        flash('The post has been updated.')
        return redirect(url_for('.post', id=post.id))
    form.body.data = post.body
    return render_template('edit_post.html', form=form)


@main.route('/follow/<username>')
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('.index'))
    if current_user.is_following(user):
        flash('You are already following this user.')
        return redirect(url_for('.user', username=username))
    current_user.follow(user)
    flash('You are now following %s.' % username)
    return redirect(url_for('.user', username=username))


@main.route('/unfollow/<username>')
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('.index'))
    if not current_user.is_following(user):
        flash('You are not following this user.')
        return redirect(url_for('.user', username=username))
    current_user.unfollow(user)
    flash('You are not following %s anymore.' % username)
    return redirect(url_for('.user', username=username))

