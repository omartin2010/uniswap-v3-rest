import json
from univ3.UNI_v3_support_funcs import get_eth_usd, univ3_position #  univ3_pool, univ3_position

pos = univ3_position('166439')
print(f'get_eth_usd = {get_eth_usd()}')
print(f'unclaimed = {pos.get_uncollected_fees()}')
# pos._calculate_uncollected_fees_2()
# print(f'tok0 = ={pos._last_feetoken0}')
# print(f'tok1 = ={pos._last_feetoken1}')
# print(pos.describe_position())

output = json.dumps(pos.describe_position())
print(output)

toks = pos.add_to_position_split(2100, 0.54)
print(toks)