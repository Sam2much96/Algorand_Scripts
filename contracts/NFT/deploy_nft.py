import json
import base64
from algosdk import account
from algosdk import mnemonic
from algosdk.v2client import algod
#from algosdk.future import transaction
from algosdk.future.transaction import AssetConfigTxn, wait_for_confirmation

 
import algosdk.algod as algod2





__account: str=""
__mnemonic : str =""
#mnemonic : str ="rigid" #8 bytes per word


"Creates an Algod Node Object"
def create_algod_testnet_client():
    # test-net
    #algod_address = 'https://testnet-algorand.api.purestake.io/ps2'#"https://node.testnet.algoexplorerapi.io" #"

    


    algod_address = "https://node.testnet.algoexplorerapi.io" #"

    algod_token = ""
    
    headers={'User-Agent': 'DoYouLoveMe?'} #work Around https://github.com/algorand/py-algorand-sdk/issues/169

    algod_client = algod.AlgodClient(algod_token, algod_address, headers)
    

    return algod_client


def create_algod_sandbox():
    #local host
    algod_address = "http://localhost:4001"
    algod_token = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    algod_client = algod.AlgodClient(algod_token, algod_address)


# creates an nft transaction
def create_nft_transacton(_mnemonic, _address):
    


    algod_client=create_algod_testnet_client()


    params = algod_client.suggested_params()

    accounts = {}
    accounts[1] = {}
    accounts[1]['pk'] = mnemonic.to_public_key(_mnemonic) #saves the new account's address
    accounts[1]['sk'] = mnemonic.to_private_key(_mnemonic) #saves the new account's mnemonic


    txn =AssetConfigTxn(sender=accounts[1]['pk'],
                        sp=params,
                        total=1,           # NFTs have totalIssuance of exactly 1
                        default_frozen=False,
                        unit_name="WAIF_001",
                        asset_name="Algo Waifu 001",
                        manager=None,
                        reserve=None,
                        freeze=False,
                        clawback="",
                        url="ipfs://QmNoThogc1D7XCzQrjePPxChyGmuohX6LXqDTCLJwTUUfR", #NFT Metadata or asset url
                        metadata_hash=None,
                        decimals=0,
                        strict_empty_address_check=False)        # NFTs have decimals of exactly 0

    # sign transaction
    
   
    
    #  Error: algosdk.error.WrongKeyBytesLengthError: key length in bytes must be 32
    signed_txn = txn.sign(accounts[1]['sk'])

     # submit transaction
    txid = algod_client.send_transaction(signed_txn)
    print("Signed transaction with txID: {}".format(txid))

    # wait for confirmation 
    try:
        confirmed_txn = wait_for_confirmation(algod_client, txid, 4)  
    except Exception as err:
        print(err)
        return
    
    print("Transaction information: {}".format(
        json.dumps(confirmed_txn, indent=4)))
    print("Decoded note: {}".format(base64.b64decode(
        confirmed_txn["txn"]["txn"]["note"]).decode()))

    print("Starting Account balance: {} microAlgos".format(account_info.get('amount')) )
    #print("Amount transfered: {} microAlgos".format(amount) )    
    print("Fee: {} microAlgos".format(params.fee) ) 


    account_info = algod_client.account_info(__account)
    idx = 0
    for my_account_info in account_info['assets']:
        scrutinized_asset = account_info['assets'][idx]
        idx = idx + 1        
        if (scrutinized_asset['asset-id'] == assetid):
            print("Asset ID: {}".format(scrutinized_asset['asset-id']))
            print(json.dumps(scrutinized_asset, indent=4))
            break





# Debugger
def debugAPI():
    algod_client=create_algod_testnet_client()

    algod_client.headers={'User-Agent': 'DoYouLoveMe?'}

    print(algod_client.__dict__)

    print(algod_client.suggested_params()) #code breaks here if not working

   




create_nft_transacton(__mnemonic,__account)
