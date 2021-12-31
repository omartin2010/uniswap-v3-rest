"""
Created on Fri Dec 24 2021 21:41 EST

@author: ape-ron
"""

''' Support functions for uniswap v3 math and requests on positions '''

import numpy as np
import requests
from .UNI_v3_funcs import amounts_relation, get_amounts

uniswap_headers = {}
uniswap_graphql_url = 'https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3'

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

    def __init__(self, __position_id:int) -> None:
        global uniswap_graphql_url
        global uniswap_headers

        self._position_id = int(__position_id)

        position_query = '''
        {
            position(id:''' + str(self._position_id) + ''') {
                liquidity
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
        else:
            print("req failed.")
            return
        
        self._lower_tick = int(lowerTick)
        self._upper_tick = int(upperTick)
        self._liquidity = int(liquidity)
        self._pool = univ3_pool(str(pool_id))

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

    def _calculate_uncollected_fees(self):
        global uniswap_graphql_url
        global uniswap_headers

        """ returns fees for token0 and token1 for position id """
        fee_query = '''
        {
        positions(where: {id:"''' + str(self._position_id) + '''"}) 
        {
            liquidity
            token0 {symbol decimals}
            token1 {symbol decimals}
            pool {feeGrowthGlobal0X128 feeGrowthGlobal1X128}
            feeGrowthInside0LastX128
            feeGrowthInside1LastX128
            tickLower {feeGrowthOutside0X128 feeGrowthOutside1X128}
            tickUpper {feeGrowthOutside0X128 feeGrowthOutside1X128}
        }
        }'''
        get = requests.post(
                url=uniswap_graphql_url,
                json={'query': fee_query},
                headers=uniswap_headers)

        if (get.status_code == 200):
            output = get.json()

            feeGrowthGlobal0X128 = int(output['data']['positions'][0]['pool']['feeGrowthGlobal0X128'])
            feeGrowthGlobal1X128 = int(output['data']['positions'][0]['pool']['feeGrowthGlobal1X128'])

            feeGrowthOutside0X128_lower = int(output['data']['positions'][0]['tickLower']['feeGrowthOutside0X128'])
            feeGrowthOutside1X128_lower = int(output['data']['positions'][0]['tickLower']['feeGrowthOutside1X128'])

            feeGrowthOutside0X128_upper = int(output['data']['positions'][0]['tickUpper']['feeGrowthOutside0X128'])
            feeGrowthOutside1X128_upper = int(output['data']['positions'][0]['tickUpper']['feeGrowthOutside1X128'])

            feeGrowthInside0LastX128 = int(output['data']['positions'][0]['feeGrowthInside0LastX128'])
            feeGrowthInside1LastX128 = int(output['data']['positions'][0]['feeGrowthInside1LastX128'])

            position_liquidity = int(output['data']['positions'][0]['liquidity'])
            decimals_tok_0 = int(output['data']['positions'][0]['token0']['decimals'])
            decimals_tok_1 = int(output['data']['positions'][0]['token1']['decimals'])

            # Calculate uncollected fees
            feetoken0 = ((feeGrowthGlobal0X128 - feeGrowthOutside0X128_lower - feeGrowthOutside0X128_upper - feeGrowthInside0LastX128)/(2**128))*position_liquidity/(1*10**decimals_tok_0)
            feetoken1 = ((feeGrowthGlobal1X128 - feeGrowthOutside1X128_lower - feeGrowthOutside1X128_upper - feeGrowthInside1LastX128)/(2**128))*position_liquidity/(1*10**decimals_tok_1)
            self._last_feetoken0 = feetoken0
            self._last_feetoken1 = feetoken1
        else: 
            print("req failed.")
            return None

    def get_uncollected_fees(self):
        self._calculate_uncollected_fees()
        return [self._last_feetoken0, self._last_feetoken1]

    def get_liquidity(self):
        current_tick = self.get_tick_at_price(self.pool.token0Price)
        toks = get_amounts(current_tick, self._lower_tick, self._upper_tick, self._liquidity, 6, 18)
        self._last_liquidity_token0 = toks[0]
        self._last_liquidity_token1 = toks[1]

    def describe_position(self):
        '''describes the important features of the position'''
        self._calculate_uncollected_fees()
        self.get_liquidity()
        output = {}
        # output['liquidity'] = self._liquidity
        output['position_configuration']={}
        output['uncollected_tokens']={}
        output['liquidity_amounts']={}
        output['price']={}
        
        output['position_configuration']['upper_tick'] = self._upper_tick
        output['position_configuration']['lower_tick'] = self._lower_tick
        output['position_configuration']['pool_id'] = self.pool._pool_id
        output['uncollected_tokens']['token0'] = self._last_feetoken0
        output['uncollected_tokens']['token1'] = self._last_feetoken1
        output['liquidity_amounts']['token0'] = self._last_liquidity_token0
        output['liquidity_amounts']['token1'] = self._last_liquidity_token1
        output['price']['token0'] = self.pool.token0Price
        output['price']['token1'] = self.pool.token1Price
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


