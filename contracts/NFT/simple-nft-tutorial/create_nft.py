import os
from pathlib import Path

import base64

from algosdk.v2client import algod
from algosdk.future import transaction
#from dotenv import load_dotenv

# Configurable parameters
TOTAL_SUPPLY = 1  # 1 denotes "NFT", more than 1 denotes a token or coin
YOUR_UNIT_NAME = "achoo"
YOUR_ASSET_NAME = "achoocoin"
YOUR_CID = ""
YOUR_URL = "http://localhost:8000/body.json"# Generally prefixed with ipfs://[your-CID]


def create_algod_client():
    address = "http://localhost:4001"
    
    token = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    algod_client = algod.AlgodClient(token, address)
    return algod.AlgodClient(token, address)


# Create an asset (your nft/memecoin)
def create_asa():
    # Load secrets from .env file
    #private_key = os.getenv("ALGORAND_SECRET")
    #address = os.getenv("ALGORAND_ADDRESS")

    private_key = "rigid steak better media circle nothing range tray firm fatigue pool damage welcome supply police spoon soul topic grant offer chimney total bronze able human",
    address = "2NFCY7HBAFJ5YP7TXUOFHHMGAZ7AHEXPS5F3NENXSC3WXRVATBR4Y23AUM"

    # Create client to send requests
    client = create_algod_client()

    # Build a transaction to create the asset
    txn = transaction.AssetConfigTxn(
        sender=address,
        sp=client.suggested_params(),
        total=TOTAL_SUPPLY,
        default_frozen=False,
        unit_name=YOUR_UNIT_NAME,
        asset_name=YOUR_ASSET_NAME,
        manager="",
        reserve="",
        freeze="",
        clawback="",
        url=YOUR_URL,
        # metadata_hash="",
        strict_empty_address_check=False,
        decimals=0,
    )

    # Sign the transaction with our private key to confirm that this transaction 
    # was authorized by us.
    #signed_txn = txn.sign(private_key=private_key)

    private_key=private_key

    print (private_key)

    signed_txn = txn.sign(base64.b64encode(private_key.encode('ascii')))

    # Send the transaction to the network using Purestake API
    txid = client.send_transaction(signed_txn)
    print("Waiting for block...")
    resp = transaction.wait_for_confirmation(client, txid, 5)

    # Let's use str.format for python <3.7 compatibility...
    # print("Successfully sent transaction with txID: {}".format(txid))
    # print("Response: {}".format(resp))
    print("Your Asset ID: {}".format(resp['asset-index']))
    #print("You can check out your asset on IPFS here: https://ipfs.io/ipfs/{}".format(YOUR_CID))
    print("Go to Algoexplorer to look at your beautiful asset: https://testnet.algoexplorer.io/asset/{}".format(resp['asset-index']))


if __name__ == "__main__":
    #load_dotenv()
    create_asa()
