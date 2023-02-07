#!/usr/bin/env python3
# *************************************************
# godot3-Dystopia-game by INhumanity_arts
# Released under MIT License
# *************************************************
# Box Storage Escrow Smart Contract
#
# An ARC 4 Abi Smart Contract
# THe Entire SmartContract Logic in one File.
# 
# Features:
# (1) Box Storage
# (2) Withdrawals
# (3) Deposit
# (4) NFT minting

# To Do:
# (1) Onchain Method Call 

from pyteal import *
from beaker import *

import base64
import hashlib
from base64 import b64encode, b64decode

from typing import Final

#from beaker.lib.storage import Mapping


#beaker documentation : https://algorand-devrel.github.io/beaker/html/application_client.html


from algosdk.v2client import algod
from algosdk import mnemonic
from beaker.client.application_client import ApplicationClient
from beaker.client.logic_error import LogicException
from beaker.consts import Algos

from beaker.lib.storage import Mapping

import json
from simple_smart_contract import create_app, compile_program, call_app, delete_app, pay, call_app_method, pay_construct

from algosdk.future import transaction
from algosdk.abi import Contract


# Arc 4 Smart Contract

class BoxEscrow(Application):

    #uses nonce https://www.investopedia.com/terms/n/nonce.asp
    hashed_secret: Final[ApplicationStateValue] = ApplicationStateValue(
        stack_type=TealType.bytes,
        descr="A scratch for saving secret nonce to application state",
    )
    
    #store transaction details to  boxes
    
 
    
    #Bare app calls https://pyteal.readthedocs.io/en/stable/abi.html?highlight=registrable%20methods#registering-bare-app-calls
    @Subroutine(TealType.none)  
    def assert_sender_is_creator() -> Expr:
        return Seq(Assert(Txn.sender() == Global.creator_address()))



    # move any balance that the user has into the "lost" amount when they close out or clear state
    transfer_balance_to_lost = App.globalPut(
        Bytes("lost"),
        App.globalGet(Bytes("lost")) + App.localGet(Txn.sender(), Bytes("balance")),
    )

    # Allocate a box called "BoxA" of byte size 100 and ignore the return value
    # "Pop()" Discards the return value 
    # Docs: https://developer.algorand.org/docs/get-details/dapps/smart-contracts/apps/#passing-arguments-to-smart-contracts
    #create_storage_boxes = Seq(
    #    #Pop(App.box_create(Bytes("BoxA"), Int(100))),
    #    Pop(App.box_create(Bytes("BoxB"), Int(50))),
    #    #Pop(App.box_create(Bytes("BoxC"), Int(100)))
    #    )
                
                
                
    """
    Docs:
        https://pyteal.readthedocs.io/en/stable/abi.html?highlight=call_config#registering-methods
 
    """
    
    my_router = Router(
    name="AlgoBank",
    bare_calls=BareCallActions(
        # approve a creation no-op call 
        #no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE),
        no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE),
        # approve opt-in calls during normal usage, and during creation as a convenience for the creator
        opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL),
        # move any balance that the user has into the "lost" amount when they close out or clear state
        close_out=OnCompleteAction(
            action=transfer_balance_to_lost, call_config=CallConfig.CALL
        ),
        clear_state=OnCompleteAction(
            action=transfer_balance_to_lost, call_config=CallConfig.CALL
        ),
        # only the creator can update or delete the app
        update_application=OnCompleteAction(
            action=assert_sender_is_creator, call_config=CallConfig.CALL
        ),
        delete_application=OnCompleteAction(
            action=assert_sender_is_creator, call_config=CallConfig.CALL
            ),
        ),
    )

    @my_router.method(no_op=CallConfig.CALL, opt_in=CallConfig.CALL)
    def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:
        """This method receives a payment from an account opted into this app and records it as a deposit.

        The caller may opt into this app during this call.

        Args:
            payment: A payment transaction containing the amount of Algos the user wishes to deposit.
                The receiver of this transaction must be this app's escrow account.
            sender: An account that is opted into this app (or will opt in during this method call).
                The deposited funds will be recorded in this account's local state. This account must
                be the same as the sender of the `payment` transaction.
        """
        return Seq(
            Assert(payment.get().sender() == sender.address()),
            Assert(payment.get().receiver() == Global.current_application_address()),



        # write to box `A` with new value
        # Deposit Address
        App.box_put(Bytes("BoxA"), sender.address())

        )



    @my_router.method
    def getBalance(user: abi.Account, *, output: abi.Uint64) -> Expr:
        """Lookup the balance of a user held by this app.

        Args:
            user: The user whose balance you wish to look up. This user must be opted into this app.

        Returns:
            The balance corresponding to the given user, in microAlgos.
        """


        return output.set(App.localGet(user.address(), Bytes("balance")))


    @my_router.method
    def withdraw(amount: abi.Uint64, recipient: abi.Account) -> Expr:
        """Withdraw an amount of Algos held by this app.

        The sender of this method call will be the source of the Algos, and the destination will be
        the `recipient` argument.

        The Algos will be transferred to the recipient using an inner transaction whose fee is set
        to 0, meaning the caller's transaction must include a surplus fee to cover the inner
        transaction.

        Args:
            amount: The amount of Algos requested to be withdraw, in microAlgos. This method will fail
                if this amount exceeds the amount of Algos held by this app for the method call sender.
            recipient: An account who will receive the withdrawn Algos. This may or may not be the same
                as the method call sender.
        """
        return Seq(

            If(Txn.sender() != Global.creator_address()) 

            .Then( 

                InnerTxnBuilder.Begin(),
                InnerTxnBuilder.SetFields(
                    {
                        TxnField.type_enum: TxnType.Payment,
                        TxnField.receiver: recipient.address(),
                        TxnField.amount: amount.get(),
                        TxnField.fee: Int(0),
                    }
                ),
                InnerTxnBuilder.Submit(),

                # write to box `B` with new value "Withdrawal Amount"
                # converted from an Integer to a Byte
                #App.box_put(Bytes("BoxB"), Itob(amount.get())),
                Pop(App.box_create(Bytes("BoxB"), Int(100))),
                App.box_put(Bytes("BoxB"), Itob(amount.get()))

                # write to box `C` with new value "Withdrawal To Address"
                #App.box_put(Bytes("BoxC"), recipient.address())
                )
            .ElseIf( Txn.sender() == Global.creator_address())
            .Then(Approve())
        )


    
    # Disabled
    #@my_router.method
    #def method_call() -> Expr:
    #    """
    #    Triggers an Abi method call via smartcontracts


    #    Args:
    #        Abi Arguments to this method

    #    Docs: https://pyteal.readthedocs.io/en/stable/api.html?highlight=MethodCall#pyteal.InnerTxnBuilder.MethodCall

    #    """




    @my_router.method
    def mint(recipient : abi.Account) -> Expr:
        """Mints an Asset Token To a Recipient Wallet Address
            the caller's transaction must include a surplus fee to cover the inner
            transaction

        Args:
            recipient: An account who will receive the withdrawn Algos. This may or may not be the same 
            as the method call sender.

        Docs: https://pyteal.readthedocs.io/en/stable/api.html#pyteal.TxnExpr

        """

        return Seq(
            InnerTxnBuilder.Begin(),
            InnerTxnBuilder.SetFields(
                {
                    TxnField.type_enum: TxnType.AssetConfig,
                    TxnField.config_asset_url : Bytes("ipfs://QmXYApu5uDsfQHMx149LWJy3x5XRssUeiPzvqPJyLV2ABx"), #CryptoPunk Asset CID
                    TxnField.config_asset_name : Bytes("Dystopia 000s"),
                    TxnField.config_asset_total : Int(1),
                    TxnField.config_asset_unit_name : Bytes("D_000"),
                    TxnField.fee : Int (0),
                    TxnField.receiver : recipient.address()

                    #asset recepient
                }
            ),
            InnerTxnBuilder.Submit(),
        )



    approval_program, clear_state_program, contract = my_router.compile_program(
        version=8, optimize=OptimizeOptions(scratch_slots=True)
    )





    """
    Write Out the Approval and Clear Programs. 
    Dump the Contract's method to a .json file.

    """

    with open("algobank_approval.teal", "w") as f:
        f.write(approval_program)

    with open("algobank_clear_state.teal", "w") as f:
        f.write(clear_state_program)
        
    with open("algobank.json", "w") as f:
        f.write(json.dumps(contract.dictify(), indent=4))









    

# Sha 265 Hashes a String
def sha256b64(s: str) -> str:
    return base64.b64encode(hashlib.sha256(str(s).encode("utf-8")).digest()).decode("utf-8")

#Configured to Testnet
#
#
def create_algorand_node_and_acct(command: str):
    
    # test-net
    algod_address = "https://node.testnet.algoexplorerapi.io"
    algod_token = ""
    algod_client = algod.AlgodClient(algod_token, algod_address)



    _params = algod_client.suggested_params()

    __mnemonic : str = "tank game arrive train bring taxi tackle popular bacon gasp tell pigeon error step leaf zone suit chest next swim luggage oblige opinion about execute"

    __mnemonic_2 : str = "degree feature waste gospel screen near subject boost wreck proof caution hen adapt fiber fault level blind entry also embark oval board bunker absorb garage"

    
    #_params.fee = 100


    #rewrite for testnet
    #client = sandbox.get_algod_client()

    #accts = sandbox.get_accounts()

    accts = {}
    accts[1] = {}
    accts[1]['pk'] = mnemonic.to_public_key(__mnemonic) #saves the new account's address
    accts[1]['sk'] = mnemonic.to_private_key(__mnemonic) #saves the new account's mnemonic
    
    mnemonic_obj_a1 = mnemonic.to_private_key(__mnemonic)
    mnemonic_obj_a2 = mnemonic.to_public_key(__mnemonic)
    
    #acct = accts.pop()

    print('Algod Client Status: ',algod_client.status())

    print (accts[1])

    #other accounts
    accts[2] = {}
    accts[2]['pk'] = mnemonic.to_public_key(__mnemonic_2)
    accts[2]['sk'] = mnemonic.to_private_key(__mnemonic_2)


    mnemonic_obj_b1 = mnemonic.to_private_key(__mnemonic_2)
    mnemonic_obj_b2 = mnemonic.to_public_key(__mnemonic_2)
    

    escrow_address = "MBUZB6RELBF6TYLWB3WT5W25GDA26FBXJZONKN54XQP2QCY2CXIFSQOBU4" #can't figure out how to determine this yet, except through chainalysis.
    # Create an Application client containing both an algod client and my app
    
    app_client = algod.AlgodClient(algod_token, algod_address,headers={'User-Agent': 'DoYouLoveMe?'})


    _app_id : int = 157575009  


    print('Algod Client Status: ',algod_client.status())

    command = input("Enter command  [deploy,pay,withdraw,deposit,mint,method_call,balance]  ")
    
    "*****************Perform Transactions Operations**********************"

    match command:
        case "deploy":

            



            "Deploy Smart Contract"
            deploy(_params, accts[1]['sk'],algod_client, 2500)
        case "delete":
    
            "Delete Smart Contract"
            delete_app(algod_client, accts[1]['sk'], _app_id)
        case "pay" :
        

            "Pay to Smart Contract"
            pay(algod_client, accts[1]['sk'], escrow_address, 1101101)
    
        case "call app":
    
           "Call SmartContract"
           call_app(algod_client, accts[2]['sk'], _app_id, "withdraw(0,RJ6STB3FL6VNNRSIMA3K5EU4DQIJJ6FAZEOIHQZA7B4GGUNLU4VSXACWYY)void")

        case "withdraw":
    
            
            call_app_method(app_client,accts[2]['sk'],_app_id, 2500,get_method("withdraw"), 0,accts[2]['pk'] )

            #txn = pay_construct(app_client, accts[1]['sk'], "MBUZB6RELBF6TYLWB3WT5W25GDA26FBXJZONKN54XQP2QCY2CXIFSQOBU4", 100_000)
        
        case "deposit":

               # create a Signer Object
            signer = AccountTransactionSigner(__mnemonic_2)

            #txn = transaction.PaymentTxn(accts[2]['pk'], _params, _app_id, 101000)

            #txn = abi.PaymentTransaction

            call_app_method(app_client,accts[2]['sk'],_app_id, 2500,get_method("deposit"), txn ,accts[2]['pk'] )


        case "mint":

            call_app_method(app_client,accts[2]['sk'],_app_id, 2500,get_method("mint"), 0,accts[2]['pk'] )


        case "method_call":

            # Calls a smartcontract Abi call via a Bare Call app txn

            call_app(app_client,accts[2]['sk'],_app_id, 2500,get_method("method_call"), 0,accts[2]['pk'] )

        case "balance":

            call_app_method(app_client,accts[2]['sk'],_app_id, 2500,get_method("balance"), 0,accts[2]['pk'] )



        case other:
            print ("No Match Found, Please Pass a Valid command to this Method in ln 309")


# Utility function to get the Method object for a given method name
def get_method(name: str) :
    with open("algobank.json") as f:
        js = f.read()
    c = Contract.from_json(js)
    for m in c.methods:
        if m.name == name:
            print ("M: ",m.name)
            return m
    raise Exception("No method with the name {}".format(name))



def deploy(_params, mnemonic_ ,algod_client, fee):

    _params.flat_fee = True
    _params.fee = fee


    # declare application state storage (immutable)
    local_ints = 0
    local_bytes = 0
    global_ints = 1
    global_bytes = 1
    global_schema = transaction.StateSchema(global_ints, global_bytes)
    local_schema = transaction.StateSchema(local_ints, local_bytes)


    # Read the compiled approvl & clear programs Teal files 
    
    """
   
    """

    with open("algobank_approval.teal", "r") as f:
        approval_program = f.read()

    with open("algobank_clear_state.teal", "r") as f:
        clear_state_program= f.read()
   


    



    response = algod_client.compile(approval_program)
    print ("Raw Response =",response )
    print("Response Result = ",response['result'])
    print("Response Hash = ",response['hash'])


    # compile program to binary
    approval_program_compiled = compile_program(algod_client, approval_program)

    # compile program to binary
    clear_state_program_compiled = compile_program(algod_client, clear_state_program)


    app_id = create_app(algod_client,_params ,mnemonic_, approval_program_compiled, clear_state_program_compiled, global_schema, local_schema)

    # Create the applicatiion on chain, set the app id for the app client & store app secret
    print(f"Created App with id: {app_id} ")


"""
THE MAIN METHOD
"""

if __name__ == "__main__":
    
    #Builds the progam and deploys
    ca = BoxEscrow()
    

    # Application State Machine
    create_algorand_node_and_acct("")
    

