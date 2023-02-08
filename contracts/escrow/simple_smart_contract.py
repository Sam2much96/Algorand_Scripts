#!/usr/bin/env python3
#SImple smart contract

"""
Helpful Logic for Working on Algorand SmartContracts
Configured to Testnet

"""

# *************************************************
# Simple Smart Contract by INhumanity_Studios
# Released under MIT License
# *************************************************
# Simple SmartContract
# 
# Features:
# Contains Sampled Txn for Algorand Blockchain 
# 


from algosdk.v2client import algod
from algosdk import account
from algosdk import mnemonic
from algosdk import logic

from algosdk.future import transaction
from algosdk.atomic_transaction_composer import *

import base64


# user declared account mnemonics
__mnemonic: str= ""

__account: str=""



#approval_program_precompiled = open('./build/approval.teal')
#clear_state_program_precompiled = open('./build/clear.teal')

# user declared algod connection parameters.
# Node must have EnableDeveloperAPI set to true in its config
algod_address = "https://node.testnet.algoexplorerapi.io"
algod_token = ""


# convert 64 bit integer i to byte string
def intToBytes(i):
    return i.to_bytes(8, "big")

# helper function that converts a mnemonic passphrase into a private signing key
def get_private_key_from_mnemonic(mn):
    private_key = mnemonic.to_private_key(mn)
    return private_key


# helper function to compile program source
def compile_program(client, source_code):
    compile_response = client.compile(source_code)
    return base64.b64decode(compile_response['result'])

# helper function that converts a mnemonic passphrase into a private signing key
def get_private_key_from_mnemonic(mn) :
    private_key = mnemonic.to_private_key(mn)
    return private_key


# helper function that formats global state for printing
def format_state(state):
    formatted = {}
    for item in state:
        key = item['key']
        value = item['value']
        formatted_key = base64.b64decode(key).decode('utf-8')
        if value['type'] == 1:
            # byte string
            if formatted_key == 'voted':
                formatted_value = base64.b64decode(value['bytes']).decode('utf-8')
            else:
                formatted_value = value['bytes']
            formatted[formatted_key] = formatted_value
        else:
            # integer
            formatted[formatted_key] = value['uint']
    return formatted

# helper function to read app global state
def read_global_state(client, app_id):
    app = client.application_info(app_id)
    global_state = app['params']['global-state'] if "global-state" in app['params'] else []
    return format_state(global_state)


# helper function that waits for a given txid to be confirmed by the network
def wait_for_confirmation(client, txid):
    last_round = client.status().get("last-round")
    txinfo = client.pending_transaction_info(txid)
    while not (txinfo.get("confirmed-round") and txinfo.get("confirmed-round") > 0):
        print("Waiting for confirmation...")
        last_round += 1
        client.status_after_block(last_round)
        txinfo = client.pending_transaction_info(txid)
    print(
        "Transaction {} confirmed in round {}.".format(
            txid, txinfo.get("confirmed-round")
        )
    )

def get_application_address(appID : int) -> str:
    return logic.get_application_address(appID)


def pay_construct( client , sender, receiver, private_key, amount):
       
    # Create signer object
    signer = AccountTransactionSigner(private_key)

    # Get suggested params from the client
    sp = client.suggested_params()

    # Create a transaction
    ptxn = transaction.PaymentTxn(sender, sp, receiver, amount)

    # Construct TransactionWithSigner
    tws = TransactionWithSigner(ptxn, signer)

    # Pass TransactionWithSigner to ATC
    #atc.add_transaction(tws)

    return tws


def pay( client , private_key, receipent, amount):
   # declare sender
    sender = account.address_from_private_key(private_key)
    print("Call from account:", sender)

    # get node suggested parameters
    params = client.suggested_params()
    # comment out the next two (2) lines to use suggested fees
    
    #params.flat_fee = True
    #params.fee = 1000

    #app_args.encode('utf-8')
    # create unsigned transaction
    #txn = transaction.ApplicationNoOpTxn(sender, params, index, app_args)

    txn = transaction.PaymentTxn(sender, params, receipent, amount)

    print("App Pay txn: ", txn)


    # sign transaction
    signed_txn = txn.sign(private_key)
    tx_id = signed_txn.transaction.get_txid()

    # send transaction
    client.send_transactions([signed_txn])

    # await confirmation
    wait_for_confirmation(client, tx_id)

# Call application method
# using Atomic Transaction composer
# use Atomic Transaction Composer to construct method call to ABI method
#https://developer.algorand.org/docs/get-details/atc/?from_query=atomic%20tr#template-modal-overlay
# The entire Smart Contract Uses 3 Boxes in line 207
def call_app_method(client, private_key, index, fee, _method, arg1, arg2):
    # get sender address
    sender = account.address_from_private_key(private_key)

    # create a Signer Object
    signer = AccountTransactionSigner(private_key)

    params = client.suggested_params()

    params.flat_fee = True
    params.fee = fee

    # create an instance of AtomicTransactionComposer
    atc = AtomicTransactionComposer()
    atc.add_method_call(
        app_id = index,
        method= _method, #contract.get_method_by_name(_method),
        sender = sender,
        sp = params,
        signer = signer,
        method_args = [arg1,arg2],
        boxes = [[0, "BoxA"],[0, "BoxB"],[0, "BoxC"], [0,""],[0,""],[0,""]], #https://developer.algorand.org/docs/get-details/dapps/smart-contracts/apps/#smart-contract-arrays

        )

        

    #send transaction
    results = atc.execute(client, 2)

    #wait for confirmation
    print("TXID: ", results.tx_ids[0])
    print("Result confirmed in round: {}".format(results.confirmed_round))

def update_app(algod_client, app_id, params,private_key,approval_program_compiled, clear_state_program_compiled):

    sender = account.address_from_private_key(private_key)

    # compile program to binary
    #approval_program_compiled = compile_program(algod_client, approval_program)

    # compile program to binary
    #clear_state_program_compiled = compile_program(algod_client, clear_state_program)




    # create unsigned transaction
    txn = transaction.ApplicationUpdateTxn(
        sender= sender, 
        sp =params, 
        index= app_id, 
        approval_program= approval_program_compiled, 
        clear_program= clear_state_program_compiled,
        boxes=[[0, "BoxA"],[0, "BoxB"],[0, "BoxC"], [0,""],[0,""],[0,""]],
        )

    # sign, send, await 

    # sign transaction
    signed_txn = txn.sign(private_key)
    tx_id = signed_txn.transaction.get_txid()

    # send transaction
    algod_client.send_transactions([signed_txn])

    # await confirmation
    wait_for_confirmation(algod_client, tx_id)



    # display results
    transaction_response = algod_client.pending_transaction_info(tx_id)
    app_id = transaction_response['txn']['txn']['apid']
    print("Updated existing app-id: ",app_id)




# call application
def call_app(client, private_key, index, app_args):
    # declare sender
    sender = account.address_from_private_key(private_key)
    print("Call from account:", sender)

    # get node suggested parameters
    params = client.suggested_params()
    # comment out the next two (2) lines to use suggested fees
    
    params.flat_fee = True
    params.fee = 1000

    #app_args.encode('utf-8')
    # create unsigned transaction
    txn = transaction.ApplicationNoOpTxn(sender, params, index, app_args)


    print("App call txn: ", txn)


    # sign transaction
    signed_txn = txn.sign(private_key)
    tx_id = signed_txn.transaction.get_txid()

    # send transaction
    client.send_transactions([signed_txn])

    # await confirmation
    wait_for_confirmation(client, tx_id)






# opt-in to application
def opt_in_app(client, private_key, index):
    # declare sender
    sender = account.address_from_private_key(private_key)
    print("OptIn from account: ", sender)

    # get node suggested parameters
    params = client.suggested_params()
    # comment out the next two (2) lines to use suggested fees
    #params.flat_fee = True
    #params.fee = 1000

    # create unsigned transaction
    txn = transaction.ApplicationOptInTxn(sender, params, index)

    # sign transaction
    signed_txn = txn.sign(private_key)
    tx_id = signed_txn.transaction.get_txid()

    # send transaction
    client.send_transactions([signed_txn])

    # await confirmation
    wait_for_confirmation(client, tx_id)

    # display results
    transaction_response = client.pending_transaction_info(tx_id)
    print("OptIn to app-id:", transaction_response["txn"]["txn"]["apid"])





# delete application
def delete_app(client, private_key, index):
    # declare sender
    sender = account.address_from_private_key(private_key)

    # get node suggested parameters
    params = client.suggested_params()
    # comment out the next two (2) lines to use suggested fees
    #params.flat_fee = True
    #params.fee = 1000

    # create unsigned transaction
    txn = transaction.ApplicationDeleteTxn(
        sender= sender, 
        sp= params, 
        index= index,
        boxes=[[0, "BoxA"],[0, "BoxB"],[0, "BoxC"], [0,""],[0,""],[0,""]],
        )

    # sign transaction
    signed_txn = txn.sign(private_key)
    tx_id = signed_txn.transaction.get_txid()

    # send transaction
    client.send_transactions([signed_txn])

    # await confirmation
    wait_for_confirmation(client, tx_id)

    # display results
    transaction_response = client.pending_transaction_info(tx_id)
    print("Deleted app-id:", transaction_response["txn"]["txn"]["apid"])


# close out from application
def close_out_app(client, private_key, index):
    # declare sender
    sender = account.address_from_private_key(private_key)

    # get node suggested parameters
    params = client.suggested_params()
    # comment out the next two (2) lines to use suggested fees
    #params.flat_fee = True
    #params.fee = 1000

    # create unsigned transaction
    txn = transaction.ApplicationCloseOutTxn(sender, params, index)

    # sign transaction
    signed_txn = txn.sign(private_key)
    tx_id = signed_txn.transaction.get_txid()

    # send transaction
    client.send_transactions([signed_txn])

    # await confirmation
    wait_for_confirmation(client, tx_id)

    # display results
    transaction_response = client.pending_transaction_info(tx_id)
    print("Closed out from app-id: ", transaction_response["txn"]["txn"]["apid"])


# clear application
def clear_app(client, private_key, index):
    # declare sender
    sender = account.address_from_private_key(private_key)

    # get node suggested parameters
    params = client.suggested_params()
    # comment out the next two (2) lines to use suggested fees
    #params.flat_fee = True
    #params.fee = 1000

    # create unsigned transaction
    txn = transaction.ApplicationClearStateTxn(sender, params, index)

    # sign transaction
    signed_txn = txn.sign(private_key)
    tx_id = signed_txn.transaction.get_txid()

    # send transaction
    client.send_transactions([signed_txn])

    # await confirmation
    wait_for_confirmation(client, tx_id)

    # display results
    transaction_response = client.pending_transaction_info(tx_id)
    print("Cleared app-id:", transaction_response["txn"]["txn"]["apid"])





# create new application
def create_app(client, params, private_key, approval_program, clear_program, global_schema, local_schema):
    # define sender as creator
    sender = account.address_from_private_key(private_key)

    # declare on_complete as NoOp
    on_complete = transaction.OnComplete.NoOpOC.real

    # get node suggested parameters
    #params = client.suggested_params()

    # create unsigned transaction
    txn = transaction.ApplicationCreateTxn(sender, params, on_complete, \
                                            approval_program, clear_program, \
                                            global_schema, local_schema)

    # sign transaction
    signed_txn = txn.sign(private_key)
    tx_id = signed_txn.transaction.get_txid()

    # send transaction
    client.send_transactions([signed_txn])

    # wait for confirmation
    try:
        transaction_response = transaction.wait_for_confirmation(client, tx_id, 4)
        print("TXID: ", tx_id)
        print("Result confirmed in round: {}".format(transaction_response['confirmed-round']))

    except Exception as err:
        print(err)
        return

    # display results
    transaction_response = client.pending_transaction_info(tx_id)
    app_id = transaction_response['application-index']
    print("Created new app-id:", app_id)

    return app_id


def main() :
    # initialize an algodClient
    #always initialialize testnet with a header
    algod_client = algod.AlgodClient(algod_token, algod_address,headers={'User-Agent': 'DoYouLoveMe?'})


    print('Algod Client Status: ',algod_client.status())

    # define private keys
    #creator_private_key = get_private_key_from_mnemonic(creator_mnemonic)
    creator_private_key =mnemonic.to_private_key(__mnemonic)
    
    # Complex TEAL program. From global counter dapp teal
    #debug to make valid app calls to smartcontract
    data = """
    
    """ #accepts and rejects all transactions
    data2 = ""
    # compile teal program
    response = algod_client.compile(data)
    print ("Raw Response =",response )
    print("Response Result = ",response['result'])
    print("Response Hash = ",response['hash'])


    # declare application state storage (immutable)
    local_ints = 0
    local_bytes = 0
    global_ints = 1
    global_bytes = 1
    global_schema = transaction.StateSchema(global_ints, global_bytes)
    local_schema = transaction.StateSchema(local_ints, local_bytes)

    # compile Teal program to TEAL assembly



    # compile program to binary
    approval_program_compiled = compile_program(algod_client, data2)

    # compile program to binary
    clear_state_program_compiled = compile_program(algod_client, data)

    
    print("approval program compiled:",approval_program_compiled)


    print("--------------------------------------------")
    print("Testing Deploying Counter application......")

    


    # create new application
    #app_id = create_app(algod_client, creator_private_key, clear_state_program_compiled, clear_state_program_compiled, global_schema, local_schema) #works

   
   #delete application
   #app_id = delete_app(algod_client, creator_private_key,116639568)



   #call app
   #[105, 110, 99]
   #print ('inc'.encode())


    app_id=call_app(algod_client, creator_private_key, 116639568, ['inc'.encode()]) #works


    # read global state of application
    #print("Global state:", read_global_state(algod_client, app_id))





#main()
