from flask import Flask, jsonify, request
from univ3.UNI_v3_support_funcs import univ3_position
import dotenv

dotenv.load()
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


@app.route('/position/add_to_position_split/<position_id>', methods=['GET'])
def position_add_to_position_split(position_id: str):

    output = {}
    try:
        pos = univ3_position(int(position_id))
        token0_qty = float(request.args.get('token0'))
        token1_qty = float(request.args.get('token1'))
        new_tok0, new_tok1, sell_token1, sell_amount = \
            pos.add_to_position_split(token0_qty, token1_qty)
        output['token0'] = new_tok0
        output['token1'] = new_tok1
        if sell_token1:
            output[f'sell_{pos.pool.token1_symbol}'] = True
            output[f'sell_{pos.pool.token1_symbol}_amount'] = sell_amount
        else:
            output[f'sell_{pos.pool.token0_symbol}'] = True
            output[f'sell_{pos.pool.token0_symbol}_amount'] = sell_amount
    except:
        output['problem'] = 'Cannot figure out split.'
        output['details'] = 'Does your position even exist? Did you add token0 and token1 params?'
    return jsonify(output)

