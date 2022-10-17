#SImple smart contract

# deploys a Teal smart contract to test wallet address
# a counting contract that increments a blockchain stored number

#contains both compile and deploy logic. SHould be separated later




from algosdk.v2client import algod
from algosdk import account
from algosdk import mnemonic
#from algosdk import transaction
from algosdk.future import transaction

import base64


# user declared account mnemonics
__mnemonic: str= "tank game arrive train bring taxi tackle popular bacon gasp tell pigeon error step leaf zone suit chest next swim luggage oblige opinion about execute"

__account: str="4KMRCP23JP4SM2L65WBLK6A3TPT723ILD27R7W755P7GAU5VCE7LJHAUEQ"



approval_program_precompiled = open('./build/approval.teal')
clear_state_program_precompiled = open('./build/clear.teal')

# user declared algod connection parameters.
# Node must have EnableDeveloperAPI set to true in its config
algod_address = "https://node.testnet.algoexplorerapi.io"
algod_token = ""



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





# create new application
def create_app(client, private_key, approval_program, clear_program, global_schema, local_schema):
    # define sender as creator
    sender = account.address_from_private_key(private_key)

    # declare on_complete as NoOp
    on_complete = transaction.OnComplete.NoOpOC.real

    # get node suggested parameters
    params = client.suggested_params()

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
    data = """
    #pragma version 5
	txn ApplicationID
	int 0
	==
	bnz main_l16
	txn OnCompletion
	int DeleteApplication
	==
	bnz main_l15
	txn OnCompletion
	int UpdateApplication
	==
	bnz main_l14
	txn OnCompletion
	int OptIn
	==
	bnz main_l13
	txn OnCompletion
	int CloseOut
	==
	bnz main_l12
	txn OnCompletion
	int NoOp
	==
	bnz main_l7
	err
	main_l7:
	txna ApplicationArgs 0
	byte "inc"
	==
	bnz main_l11
	txna ApplicationArgs 0
	byte "dec"
	==
	bnz main_l10
	err
	main_l10:
	byte "counter"
	byte "counter"
	app_global_get
	int 1
	-
	app_global_put
	int 1
	return
	main_l11:
	byte "counter"
	byte "counter"
	app_global_get
	int 1
	+
	app_global_put
	int 1
	return
	main_l12:
	int 0
	return
	main_l13:
	int 0
	return
	main_l14:
	int 0
	return
	main_l15:
	int 0
	return
	main_l16:
	byte "owner"
	txn Sender
	app_global_put
	byte "counter"
	int 0
	app_global_put
	int 1
	return
    """ #accepts and rejects all transactions
    data2 = "#pragma version 5; int 1; return"
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

    #approval_compiled = algod_client.compile(approval_program_precompiled)
    #clear_compiled = algod_client.compile(clear_state_program_precompiled)

    #with open("./approval.teal", "w") as f:
    #    f.write(approval_program)



    # compile program to TEAL assembly
    #with open("./clear.teal", "w") as f:
    #    f.write(clear_state_program)

    # compile program to binary
    approval_program_compiled = compile_program(algod_client, data2)

    # compile program to binary
    clear_state_program_compiled = compile_program(algod_client, data)

    print("--------------------------------------------")
    print("Testing Deploying Counter application......")

    # create new application
    app_id = create_app(algod_client, creator_private_key, clear_state_program_compiled, clear_state_program_compiled, global_schema, local_schema)

    # read global state of application
    print("Global state:", read_global_state(algod_client, app_id))





main()
