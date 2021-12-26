import json
from univ3.UNI_v3_support_funcs import get_eth_usd, univ3_position #  univ3_pool, univ3_position

pos = univ3_position('166439')
print(f'get_eth_usd = {get_eth_usd()}')
print(f'unclaimed = {pos.get_uncollected_fees()}')

# print(pos.describe_position())

output = json.dumps(pos.describe_position())
print(output)