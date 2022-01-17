import json
from univ3.UNI_v3_support_funcs import get_eth_usd, univ3_position #  univ3_pool, univ3_position

pos = univ3_position('166439')
# print(f'get_eth_usd = {get_eth_usd()}')
# print(f'unclaimed = {pos.get_uncollected_fees()}')
print(f'claimed fees = {pos.get_collected_fees()}')
# print(f'tok0 = ={pos._last_feetoken0}')
# print(f'tok1 = ={pos._last_feetoken1}')

output = json.dumps(pos.describe_position())
print(output)

toks = pos.add_to_position_split(2100, 0.54)
print(toks)