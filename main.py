from os import environ
from os.path import join

from flask import Flask, render_template, flash, redirect, url_for, jsonify, request
from flask_login import LoginManager, login_required, login_user, logout_user
from flask_breadcrumbs import Breadcrumbs, register_breadcrumb
from werkzeug.utils import secure_filename


from services import get_promoter, check_promoter, get_events, create_event, get_event, check_object
from forms import LoginForm, EventForm
from utils import view_event_dlc, allowed_file, upload_photo
from constants import UPLOAD_FOLDER


app = Flask(__name__)
app.config['SECRET_KEY'] = environ.get('SECRET_KEY') or 'secret'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'É necessário autenticar-se para aceder ao sistema'
login_manager.login_message_category = "warning"

breadcrumbs = Breadcrumbs()
breadcrumbs.init_app(app)


@login_manager.user_loader
def load_user(promoter_id):
    return get_promoter(promoter_id)


@app.route('/login', methods=['get', 'post'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        promoter = check_promoter(email=email, password=password)
        if promoter is None:
            flash('Credenciais inválidas.', 'danger')
        else:
            login_user(promoter)
            flash('Entrou como {}.'.format(promoter.name), 'success')
            fwd = request.args.get('next')
            if fwd:
                return redirect(fwd)
            return redirect(url_for('index'))
    return render_template('accounts/login.html', form=form)


@app.route('/logout', methods=['get'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/', methods=['get'])
@register_breadcrumb(app, '.', 'Groovin')
def index():
    return redirect(url_for('events'))


@app.route('/events', methods=['get'])
@login_required
@register_breadcrumb(app, '.events', 'Os Meus Eventos')
def events():
    return render_template('events/index.html', events=get_events())


@app.route('/events/new', methods=['get', 'post'])
@login_required
@register_breadcrumb(app, '.events.new_event', 'Novo')
def new_event():
    form = EventForm()
    if form.validate_on_submit():
        image = request.files['image']
        if image.filename == '':
            flash('Nenhuma imagem selecionada', category='danger')
            return redirect(request.url)

        if allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image_path = join(app.config['UPLOAD_FOLDER'], filename)

            # tmp save
            image.save(join(image_path))

            image_url = upload_photo(image_path)

            event = create_event(
                name=form.name.data, category=form.category.data, description=form.description.data, image_url=image_url)

            flash('Evento criada', 'success')
            return redirect(url_for('index'))
        flash('Imagem inválida', category='danger')
        return redirect(request.url)
    return render_template('events/new.html', form=form)


@ app.route('/events/<int:event_id>', methods=['get'])
@ login_required
@ register_breadcrumb(app, '.events.details', '',
                      dynamic_list_constructor=view_event_dlc)
def event(event_id):
    event = get_event(event_id=event_id)
    check_object(event)
    return render_template('events/details.html', event=event)


@ app.errorhandler(404)
def not_found(e):
    resp = jsonify(dict(error="Not Found"))
    resp.status_code = 404
    return resp


if __name__ == "__main__":
    app.run(debug=True)
