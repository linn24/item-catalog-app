from flask import Flask, render_template, request
from flask import redirect, url_for, jsonify, flash

from database_setup import Base, Category, Item, User
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

from functools import wraps

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Item Catalog Application"

engine = create_engine('sqlite:///itemcatalog.db')
Base.metadata.bind = create_engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


def login_required(f):
    """
    method/class name: check whether user has logged in
    Args:
        no argument
    Returns:
        proceed to requested page if already logged in
        redirect to login page if not logged in yet
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' in login_session:
            return f(*args, **kwargs)
        else:
            flash("You are not allowed to access there")
            return redirect('/login')
    return decorated_function


@app.route('/login')
def displayLogin():
    """
    method/class name: generate a random string and store as STATE in session
    Args:
        no argument
    Returns:
        redirect to login page
    """
    state = ''.join(random.choice(
            string.ascii_uppercase + string.digits) for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state, CLIENT_ID=CLIENT_ID)


# User Helper Functions
def createUser(login_session):
    """
    method/class name: create a new user account
                        using information stored in login session
    Args:
        login session
    Returns:
        return user ID
    """
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(
                            email=login_session['email']).one_or_none()
    return user.id


def getUserInfo(user_id):
    """
    method/class name: retrieve user information using user ID
    Args:
        user ID
    Returns:
        return user information
    """
    user = session.query(User).filter_by(id=user_id).one_or_none()
    return user


def getUserID(email):
    """
    method/class name: retrieve user ID using email address
    Args:
        email address
    Returns:
        return user ID
    """
    try:
        user = session.query(User).filter_by(email=email).one_or_none()
        return user.id
    except Exception:
        return None


@app.route('/gconnect', methods=['POST'])
def gconnect():
    """
    method/class name: google login
    Args:
        no argument
    Returns:
        return response
    """
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = (
        'https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
        % access_token
    )
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 50)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended use
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;'
    output += 'border-radius: 150px;-webkit-border-radius: 150px;'
    output += '-moz-border-radius: 150px;"> '
    flash("You are now logged in as %s" % login_session['username'])
    return output


@app.route('/gdisconnect')
def gdisconnect():
    """
    method/class name: google logout
    Args:
        no argument
    Returns:
        redirect to all categories page
    """
    access_token = login_session.get('access_token')
    if access_token is None:
        flash('Current user not connected.')

    url = (
        'https://accounts.google.com/o/oauth2/revoke?token=%s'
        % login_session['access_token']
    )
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        flash('Successfully logged out.')

    else:
        flash('Failed to revoke token for given user.')

    return redirect(url_for('showCategories'))


@app.route('/', methods=['GET'])
def showCategories():
    categories = session.query(Category)
    latest_items = session.query(Item).order_by(Item.id.desc()).limit(9)
    return render_template(
        'categories.html', categories=categories, latest_items=latest_items)


@app.route('/catalog/<string:cat_name>/items', methods=['GET'])
def showItems(cat_name):
    """
    method/class name: retrieve all items under a given category
    Args:
        category name
    Returns:
        redirect to item list page
    """
    category = session.query(Category).filter_by(name=cat_name).one_or_none()

    items = session.query(Item).filter_by(cat_id=category.id)
    item_count = len(list(items))

    if item_count < 1:
        items = []
    return render_template(
        'items.html', category=category, items=items, item_count=item_count)


@app.route('/catalog/<string:cat_name>/<string:item_title>', methods=['GET'])
def viewItem(cat_name, item_title):
    """
    method/class name: retrieve item's details
                        using category name and item title
    Args:
        category name
        item title
    Returns:
        redirect to item's details page
    """
    category = session.query(Category).filter_by(name=cat_name).one_or_none()
    item = session.query(Item).filter_by(
                                        cat_id=category.id,
                                        title=item_title).one_or_none()
    return render_template('view_item.html', item=item)


@app.route('/catalog/<string:item_title>/edit', methods=['GET', 'POST'])
@login_required
def editItem(item_title):
    """
    method/class name: retrieve/save changes to item's details
    Args:
        item title
    Returns:
        redirect to item's details page if no access
        redirect to item's details page upon saving changes
        redirect to edit page otherwise
    """
    item = session.query(Item).filter_by(title=item_title).one_or_none()

    if login_session['user_id'] != item.user_id:
        flash("You are not allowed to edit this item.")
        return redirect(url_for('viewItem',
                                cat_name=item.category.name,
                                item_title=item.title))

    if request.method == 'POST':
        if request.form['txtTitle']:
            item.title = request.form['txtTitle']
        if request.form['txtDesc']:
            item.description = request.form['txtDesc']
        if request.form['txtCat']:
            item.cat_id = request.form['txtCat']

        session.add(item)
        session.commit()

        category = session.query(Category).filter_by(
                    id=item.cat_id).one_or_none()
        return redirect(url_for('viewItem',
                                cat_name=category.name,
                                item_title=item.title))
    else:
        categories = session.query(Category)
        return render_template(
            'edit_item.html', categories=categories, item=item)


@app.route('/catalog/<string:item_title>/delete', methods=['GET', 'POST'])
@login_required
def deleteItem(item_title):
    """
    method/class name: delete a given item
    Args:
        item title
    Returns:
        redirect to item's details page if no access
        redirect to all categories page after deleting
        redirect to delete page otherwise
    """
    itemToDelete = session.query(Item).filter_by(
                    title=item_title).one_or_none()

    if login_session['user_id'] != itemToDelete.user_id:
        flash("You are not allowed to delete this item.")
        return redirect(url_for('viewItem',
                                cat_name=itemToDelete.category.name,
                                item_title=itemToDelete.title))

    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        flash(item_title + " has been deleted.")
        return redirect(url_for('showCategories'))
    else:
        return render_template('delete_item.html', item_title=item_title)


@app.route('/catalog/add', methods=['GET', 'POST'])
@login_required
def addItem():
    """
    method/class name: create a new item with given details
    Args:
        no argument
    Returns:
        redirect to item's details page after saving
        redirect to add page otherwise
    """
    if request.method == 'POST':
        item = Item(
            title=request.form['txtTitle'],
            description=request.form['txtDesc'],
            cat_id=request.form['txtCat'],
            user_id=login_session['user_id'])

        session.add(item)
        session.commit()
        return redirect(url_for('viewItem',
                                cat_name=item.category.name,
                                item_title=item.title))
    else:
        categories = session.query(Category)
        return render_template('add_item.html', categories=categories)


@app.route('/catalog.json')
def itemCatalogJSON():
    """
    method/class name: generate json for all categories and items
    Args:
        no argument
    Returns:
        serialized categories and items
    """
    categories = session.query(Category).all()
    serializedCategories = []
    for c in categories:
        cat = c.serialize
        items = session.query(Item).filter_by(cat_id=c.id).all()
        serializedItems = []
        for i in items:
            serializedItems.append(i.serialize)
        cat['Item'] = serializedItems
        serializedCategories.append(cat)
    return jsonify(Category=serializedCategories)


@app.route('/catalog/<string:item_title>/json')
def itemJSON(item_title):
    """
    method/class name: generate json for an item
    Args:
        item title
    Returns:
        serialized item
    """
    itemToSerialize = session.query(Item).filter_by(
                        title=item_title).one_or_none()
    return jsonify(Item=itemToSerialize.serialize)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
