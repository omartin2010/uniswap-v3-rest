from flask import Flask, jsonify
from univ3.UNI_v3_support_funcs import univ3_position

app = Flask(__name__)

@app.errorhandler(404)
def page_not_found(error):
    output={}
    output['problem'] = 'Undefined API method.'
    return jsonify(output), 404

@app.route('/position/describe/<position_id>', methods = ['GET'])
def position_describe(position_id: str):
    try:
        pos = univ3_position(int(position_id))
        output = pos.describe_position()
    except:
        output={}
        output['problem'] = 'Cannot create position object.'
        output['details'] = 'Does your position even exist?'
    return jsonify(output)
