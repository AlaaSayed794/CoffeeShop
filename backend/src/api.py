import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth
from werkzeug.exceptions import HTTPException

app = Flask(__name__)
setup_db(app)
CORS(app)


def validate_recipes(recipes):
    '''
    ensures recipe is valid before insertion so that database is always in clean state
    '''
    drink_recipes=[]
    if(not isinstance(recipes,list) and not isinstance(recipes,dict)):
        return None
    if(isinstance(recipes,dict)):
        try:
            name = recipes['name']
            parts = recipes['parts']
            color = recipes['color']
            if( not isinstance(name,str)):
                return None
            if( not isinstance(color,str)):
                return None
            if( not isinstance(parts,(str,int,float))):
                return None
            drink_recipes =  [{"color":color,"name":name,"parts":int(parts)}]
        except:
            return None
    else:
        for recipe in recipes:
            name = recipe['name']
            parts = recipe['parts']
            color = recipe['color']
            if( not isinstance(name,str)):
                return None
            if( not isinstance(color,str)):
                return None
            if( not isinstance(parts,(str,int,float))):
                return None
            drink_recipes.append({"color":color,"name":name,"parts":int(parts)})
    return drink_recipes

'''
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
'''
db_drop_and_create_all()

## ROUTES

@app.route('/drinks',methods=['GET'])
def get_drinks():
    '''
    GET /drinks
        it should be a public endpoint
        it should contain only the drink.short() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
    '''
    drinks = Drink.query.order_by(Drink.id).all()
    print(drinks)
    return jsonify({
            'success':True,
            'drinks':[drink.short() for drink in drinks]
            })



@app.route('/drinks-detail',methods=['GET'])
@requires_auth('get:drinks-detail')
def get_drinks_details(payload):
    '''
    GET /drinks-detail
        it should require the 'get:drinks-detail' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
    '''
    drinks = Drink.query.order_by(Drink.id).all()
    return jsonify({
            'success':True,
            'drinks':[drink.long() for drink in  drinks]
            })



@app.route('/drinks',methods=['POST'])
@requires_auth('post:drinks')
def create_drink(payload): 
    '''
    POST /drinks
        it should create a new row in the drinks table
        it should require the 'post:drinks' permission
        it requires body having {'title':title , 
        'recipe':[{'name':string , 'color':string , 'parts':number(in int,float or string format) }] }
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the newly created drink
    or appropriate status code indicating reason for failure
    '''
    try:
        body = request.get_json()  
        recipes = body.get('recipe',None)
        title = body.get('title',None)

        if(recipes is None or title is None ):
            abort(422)
        
        drink_recipes = validate_recipes(recipes)
        if(drink_recipes is None):
            abort(422)

        drink = Drink()
        drink.title = title
        drink.recipe = json.dumps(drink_recipes)
        drink.insert()
        return jsonify({
          'success':True,
          'drinks': [drink.long()]
              })
    except Exception as e:
        print(e)
        abort(422)



@app.route('/drinks/<int:id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def edit_drink(payload, id):
    '''
    PATCH /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should update the corresponding row for <id>
        it should require the 'patch:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the updated drink
        or appropriate status code indicating reason for failure
    '''
    body = request.get_json()
    drink = Drink.query.get(id)

    if drink is None:
        abort(404)

    try:
        title = body.get('title')
        recipes = body.get('recipe')
        if title is not None:
            drink.title = title

        if recipes is not None :
            drink_recipes = validate_recipes(recipes)
            if(drink_recipes is not None):
                drink.recipes = json.dumps(drink_recipes)


        drink.update()
        return jsonify({
          'success':True,
          'drinks': [drink.long()]
              })
    except:
        abort(400)

    


@app.route('/drinks/<int:id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(payload, id):
    
    '''
    DELETE /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should delete the corresponding row for <id>
        it should require the 'delete:drinks' permission
    returns status code 200 and json {"success": True, "delete": id} where id is the id of the deleted record
        or appropriate status code indicating reason for failure
    '''
    drink = Drink.query.get(id)

    if drink is None:
        abort(404)

    try:
        drink.delete()
    except:
        abort(500)

    return jsonify({
          'success':True,
          'delete': id
              })


## Error Handling

@app.errorhandler(HTTPException)
def handle_HttpException(e):
    return jsonify({
      "success": False, 
      "error": e.code,
      "message": e.name
      }), e.code


@app.errorhandler(AuthError)
def handle_AuthException(e):
    return jsonify({
      "success": False, 
      "error": e.status_code,
      "message": e.error
      }), e.status_code

