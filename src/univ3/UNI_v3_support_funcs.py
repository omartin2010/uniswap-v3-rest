"""
Created on Fri Dec 24 2021 21:41 EST

@author: ape-ron
"""

''' Support functions for uniswap v3 math and requests on positions '''

from dotenv import load_dotenv
load_dotenv('../.env')

import numpy as np
from web3.auto.infura import w3
from pathlib import Path
import requests
import datetime
from .UNI_v3_funcs import amounts_relation, get_amounts

uniswap_headers = {}
uniswap_graphql_url = 'https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3'
uniswap_contract_abi_file = 'univ3/ref/uniswap_contract_abi.json'
uniswap_contract_address = "0xC36442b4a4522E871399CD717aBDD847Ab11FE88"
null_address = "0x0000000000000000000000000000000000000000"
uniswap_contract_abi = Path(uniswap_contract_abi_file).read_text()


def get_eth_usd():
    """ returns prices of token0/tok1 and tok1/tok0 """
    query = '''
        {
          bundles {
            id
            ethPriceUSD
          }
        }    
    '''
    get = requests.post(
        url=uniswap_graphql_url,
        json={'query': query},
        headers=uniswap_headers)

    if (get.status_code == 200):
        output = get.json()
        price = output['data']['bundles'][0]['ethPriceUSD']
    else:
        print("req failed.")

    return float(price)


class univ3_pool():
    ''' object representing a pool in univ3 '''
    
    def __init__(self, pool_id:str) -> None:
        global uniswap_graphql_url
        global uniswap_headers
        self._pool_id = pool_id

        pool_query = '''
        {
            pool(id: "''' + str(self._pool_id) + '''") {
                token0 {
                    symbol
                    decimals
                }
                token1 {
                    symbol
                    decimals
                }
            }
        }
        '''
        get = requests.post(
            url=uniswap_graphql_url,
            json={'query': pool_query},
            headers=uniswap_headers)

        if (get.status_code == 200):
            pool_data = get.json()
            self._token0_symbol = str(pool_data['data']['pool']['token0']['symbol'])
            self._token1_symbol = str(pool_data['data']['pool']['token1']['symbol'])
            self._token0_decimals = int(pool_data['data']['pool']['token0']['decimals'])
            self._token1_decimals = int(pool_data['data']['pool']['token1']['decimals'])
        else:
            print("req failed.")
    
    @property
    def token0_symbol(self):
        return self._token0_symbol
    
    @property
    def token1_symbol(self):
        return self._token1_symbol
    
    @property
    def token0_decimals(self):
        return self._token0_decimals
    
    @property
    def token1_decimals(self):
        return self._token1_decimals

    @property
    def pool_id(self):
        return self._pool_id

    @property
    def token0Price(self):
        self._get_current_info()
        return self._last_token0_price

    @property
    def token1Price(self):
        self._get_current_info()
        return self._last_token1_price

    @property
    def liquidity(self):
        self._get_current_info()
        return self._last_liquidity

    def _get_current_info(self):
        """ returns prices of token0/tok1 and tok1/tok0 """
        global uniswap_graphql_url
        global uniswap_headers
        pool_query = '''
        {
        pool(id: "''' + str(self._pool_id) + '''") {
            token0Price
            token1Price
            liquidity
        }
        }
        '''
        get = requests.post(
            url=uniswap_graphql_url,
            json={'query': pool_query},
            headers=uniswap_headers)

        if (get.status_code == 200):
            pool_data = get.json()
            token0Price = float(pool_data['data']['pool']['token0Price'])
            token1Price = float(pool_data['data']['pool']['token1Price'])
            liquidity = int(pool_data['data']['pool']['liquidity'])
        else:
            print("req failed.")

        self._last_token1_price=token1Price
        self._last_token0_price=token0Price
        self._last_liquidity = liquidity
    

class univ3_position():

    ''' Class Methods '''
    @classmethod
    def get_tick_at_price(cls, price, tok_dec_s0=18, tok_dec_s1=6):
        """ defaults are in for ETH (s0 = 18 decimals)
        and USDC = 6 decimals
        """
        return int(np.floor(np.log(10**(tok_dec_s0 - tok_dec_s1)/price)/np.log(1.0001)))

    @classmethod
    def get_price_at_tick(cls, tick, tok_dec_s0=18, tok_dec_s1=6):
        """ defaults are in for ETH (s0 = 18 decimals)
        and USDC = 6 decimals
        """
        return  1/(1.0001**tick/10**(tok_dec_s0 - tok_dec_s1))

    @classmethod
    def get_eth_value_at_date(cls, current_block_date):
        """returns eth value at this date based on coingecko API"""
        
        datestr = current_block_date.strftime('%d-%m-%Y')
        req_url = f'https://api.coingecko.com/api/v3/coins/ethereum/history?date={datestr}'
        headers = {'accept': 'application/json'}
        get = requests.get(
            url=req_url,
            headers=headers)

        if (get.status_code == 200):
            output = get.json()
        else:
            print("req failed.")
        return output['market_data']['current_price']['usd']

    def __init__(self, __position_id:int) -> None:
        global uniswap_graphql_url
        global uniswap_headers
        global uniswap_contract_address
        global uniswap_contract_abi
        global null_address

        self._position_id = int(__position_id)
        self._uniswap_contract = w3.eth.contract(
            address=uniswap_contract_address, 
            abi=uniswap_contract_abi)
        self._collect_uniswap_fees = self._uniswap_contract.functions.collect(
            (self._position_id,
            null_address,
            10**32,
            10**32))
        position_query = '''
        {
            position(id:''' + str(self._position_id) + ''') {
                liquidity
                token0 {symbol decimals}
                token1 {symbol decimals}
                pool{id}
                tickLower{
                    tickIdx
                }    
                tickUpper{
                    tickIdx
                }
            }
        }
        '''

        get = requests.post(
                url=uniswap_graphql_url,
                json={'query': position_query},
                headers=uniswap_headers)

        if (get.status_code == 200):
            output_position = get.json()
            lowerTick = output_position['data']['position']['tickLower']['tickIdx']
            upperTick = output_position['data']['position']['tickUpper']['tickIdx']
            liquidity = output_position['data']['position']['liquidity']
            pool_id = output_position['data']['position']['pool']['id']
            token0_symbol = output_position['data']['position']['token0']['symbol']
            token1_symbol = output_position['data']['position']['token1']['symbol']
            token0_decimals = output_position['data']['position']['token0']['decimals']
            token1_decimals = output_position['data']['position']['token1']['decimals']
        else:
            print("req failed.")
            return
        
        self._lower_tick = int(lowerTick)
        self._upper_tick = int(upperTick)
        self._liquidity = int(liquidity)
        self._pool = univ3_pool(str(pool_id))
        self._token0_symbol = str(token0_symbol)
        self._token1_symbol = str(token1_symbol)
        self.token0_decimals = int(token0_decimals)
        self.token1_decimals = int(token1_decimals)

    @property
    def position_id(self):
        return self._position_id

    @property
    def current_tick(self):
        current_tick = self.get_tick_at_price(self.pool.token0Price)
        return current_tick

    @property
    def liquidity(self):
        return self._liquidity

    @property
    def upper_tick(self):
        return self._upper_tick
    
    @property
    def lower_tick(self):
        return self._lower_tick

    @property
    def pool(self):
        return self._pool

    def _get_uncollected_fees(self):

        feetoken0, feetoken1 = self._collect_uniswap_fees.call()
        self._last_feetoken0 = feetoken0/10**self.token0_decimals
        self._last_feetoken1 = feetoken1/10**self.token1_decimals

    def _get_collected_fees(self):
        """ figures what has been collected from ethereum events for collect """
        ef = self._uniswap_contract.events.Collect.createFilter(
            fromBlock=1, 
            argument_filters = {'tokenId':self._position_id})
        collect_events = ef.get_all_entries()
        amount0 = 0
        amount1 = 0
        for collect_event in collect_events:
            amount0 += collect_event['args']['amount0']
            amount1 += collect_event['args']['amount1']
        self._collected_feetoken0 = amount0/10**self.token0_decimals
        self._collected_feetoken1 = amount1/10**self.token1_decimals

    def get_collected_fees(self):
        """ used for testing """
        self._get_collected_fees()
        return [self._collected_feetoken0, self._collected_feetoken1]

    def get_uncollected_fees(self):
        """ used for testing """
        self._get_uncollected_fees()
        return [self._last_feetoken0, self._last_feetoken1]

    def _get_consumed_gas(self):
        
        # Retrieve transactions for this position
        txs=[]
        ef = self._uniswap_contract.events.Collect.createFilter(fromBlock=1, argument_filters=
                                                        {'tokenId':self.position_id})
        txs.extend(ef.get_all_entries())
        ef = self._uniswap_contract.events.DecreaseLiquidity.createFilter(fromBlock=1, argument_filters=
                                                    {'tokenId':self.position_id})
        txs.extend(ef.get_all_entries())
        ef = self._uniswap_contract.events.IncreaseLiquidity.createFilter(fromBlock=1, argument_filters=
                                                        {'tokenId':self.position_id})
        txs.extend(ef.get_all_entries())
        
        total_gasconsumed_eth = 0
        total_gasconsumed_usd = 0
        # loop for each tx
        for tx in txs:
            hash=tx['transactionHash'].hex()
            tx_details = w3.eth.get_transaction_receipt(hash)
            tx_eth_gas = tx_details['effectiveGasPrice']*tx_details['gasUsed']/10**18
            current_block_number = tx['blockNumber']
            current_block_timetamp = w3.eth.get_block(current_block_number)['timestamp']
            current_block_date = datetime.datetime.fromtimestamp(current_block_timetamp)
            total_gasconsumed_eth += tx_eth_gas
            total_gasconsumed_usd += tx_eth_gas * self.get_eth_value_at_date(current_block_date)
            
        self.total_gasconsumed_eth = total_gasconsumed_eth
        self.total_gasconsumed_usd = total_gasconsumed_usd


    def get_liquidity(self):
        current_tick = self.get_tick_at_price(self.pool.token0Price)
        toks = get_amounts(current_tick, self._lower_tick, self._upper_tick, self._liquidity, 6, 18)
        self._last_liquidity_token0 = toks[0]
        self._last_liquidity_token1 = toks[1]

    def describe_position(self):
        '''describes the important features of the position'''
        
        self._get_uncollected_fees()
        self._get_collected_fees()
        self.get_liquidity()
        self._get_consumed_gas()
        output = {}
        # output['liquidity'] = self._liquidity
        output['position_configuration']={}
        output['collected_tokens']={}
        output['uncollected_tokens']={}
        output['liquidity_amounts']={}
        output['price']={}
        output['gas_price']={}
        
        output['position_configuration']['upper_tick'] = self._upper_tick
        output['position_configuration']['lower_tick'] = self._lower_tick
        output['position_configuration']['pool_id'] = self.pool._pool_id
        output['collected_tokens']['collected_tokens_token0'] = self._collected_feetoken0
        output['collected_tokens']['collected_tokens_token1'] = self._collected_feetoken1
        output['uncollected_tokens']['uncollected_tokens_token0'] = self._last_feetoken0
        output['uncollected_tokens']['uncollected_tokens_token1'] = self._last_feetoken1
        output['liquidity_amounts']['liquidity_token0'] = self._last_liquidity_token0
        output['liquidity_amounts']['liquidity_token1'] = self._last_liquidity_token1
        output['price']['price_token0'] = self.pool.token0Price
        output['price']['price_token1'] = self.pool.token1Price
        output['gas_price']['gas_price_eth'] = self.total_gasconsumed_eth
        output['gas_price']['gas_price_usd'] = self.total_gasconsumed_usd

        return output
    
    def add_to_position_split(self, token0_amount: float, token1_amount: float):
        """ used to determine the amount of token0, token1 that needs to be added
        should you decide to increase your position (compounding returns when collecting fees
        to reinject in the position for example. For example, if you have 1000USD worth
        of tokens (500USDC + 0.125ETH @ 4000USD/ETH), what is the mix of tokens, at
        current price, in this position, do we need to add? - then a swap will likely 
        be necessary to get to that mix """

        ar = amounts_relation(self.current_tick, 
                              self.lower_tick,
                              self.upper_tick,
                              self.pool.token0_decimals,
                              self.pool.token1_decimals)
        
        # Get the total value of tokens proposed (USDC + ETH for example)
        usd_proposed_tokens_value = token0_amount + self.pool.token0Price * token1_amount
        required_tok0 = usd_proposed_tokens_value/(1+ar*self.pool.token0Price)
        required_tok1 = required_tok0 * ar

        if required_tok0 >= token0_amount:
            """ need to sell token1 to buy more token 0
            for example sell 0.1E to buy USDC
            """
            sell_token1 = True
            sell_amount = token1_amount - required_tok1
        else:
            """ need to sell token0 or buy token 1
            for example buy 0.1E with USDC
            """
            sell_token1 = False
            sell_amount = token0_amount - required_tok0

        return (required_tok0, required_tok1, sell_token1, sell_amount)


