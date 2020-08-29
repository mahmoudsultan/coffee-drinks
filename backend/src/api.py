import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink, db
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

'''
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
'''
# db_drop_and_create_all()

# ROUTES
'''
@TODO implement endpoint
    GET /drinks
        it should be a public endpoint
        it should contain only the drink.short() data representation
    returns status code 200 and json {"success": True, "drinks": drinks}
    where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''


@app.route('/drinks', methods=['GET'])
def index():
    drinks = Drink.query.all()
    return jsonify({
        'success': True,
        'drinks': [drink.short() for drink in drinks]
    })


'''
@TODO implement endpoint
    GET /drinks-detail
        it should require the 'get:drinks-detail' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drinks}
    where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''


@app.route('/drinks-detail', methods=['GET'])
@requires_auth('get:drinks-detail')
def drink_details(user):
    drinks = Drink.query.all()
    return jsonify({
        'success': True,
        'drinks': [drink.long() for drink in drinks]
    })


'''
@TODO implement endpoint
    POST /drinks
        it should create a new row in the drinks table
        it should require the 'post:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink}
    where drink an array containing only the newly created drink
        or appropriate status code indicating reason for failure
'''


@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def create_drink(user):
    drink_params = request.get_json()

    title = drink_params.get('title', None)
    recipe = drink_params.get('recipe', None)

    if not title or not recipe:
        abort(422)

    drink = Drink(title=title, recipe=json.dumps(recipe))
    try:
        db.session.add(drink)
        drink_view = drink.long()
        db.session.commit()

        return jsonify({
            'success': True,
            "drinks": [drink_view]
        })
    except Exception as e:
        print(str(e))
        db.session.rollback()
        abort(500)
    finally:
        db.session.close()


'''
@TODO implement endpoint
    PATCH /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should update the corresponding row for <id>
        it should require the 'patch:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink}
    where drink an array containing only the updated drink
        or appropriate status code indicating reason for failure
'''


@app.route('/drinks/<int:id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def update_drink(user, id):
    drink = Drink.query.get(id)
    if not drink:
        abort(404)

    update_params = request.get_json()

    if 'title' in update_params:
        drink.title = update_params['title']

    if 'recipe' in update_params:
        drink.recipe = json.dumps(update_params['recipe'])

    try:
        drink_view = drink.long()

        db.session.commit()

        return jsonify({
            'success': True,
            'drinks': [drink_view]
        })
    except Exception:
        db.session.rollback()
        abort(500)
    finally:
        db.session.close()


'''
@TODO implement endpoint
    DELETE /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should delete the corresponding row for <id>
        it should require the 'delete:drinks' permission
    returns status code 200 and json {"success": True, "delete": id}
    where id is the id of the deleted record
        or appropriate status code indicating reason for failure
'''


@app.route('/drinks/<int:id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(user, id):
    drink = Drink.query.get(id)
    if not drink:
        abort(404)

    try:
        db.session.delete(drink)
        db.session.commit()
        return jsonify({
            'success': True,
            "delete": id
        })
    except Exception as e:
        print(str(e))
        db.session.rollback()
        abort(500)
    finally:
        db.session.close()


# Error Handling
'''
Example error handling for unprocessable entity
'''


@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
                    "success": False,
                    "error": 422,
                    "message": "unprocessable"
                    }), 422


'''
@TODO implement error handlers using the @app.errorhandler(error) decorator
    each error handler should return (with approprate messages):
             jsonify({
                    "success": False,
                    "error": 404,
                    "message": "resource not found"
                    }), 404

'''

'''
@TODO implement error handler for 404
    error handler should conform to general task above
'''


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 404,
        'message': 'not found.'
    }), 404


'''
@TODO implement error handler for AuthError
    error handler should conform to general task above
'''


@app.errorhandler(AuthError)
def unauthorized(error):
    return jsonify({
        'success': False,
        'error': 401,
        'message': error.error
    }), 401
