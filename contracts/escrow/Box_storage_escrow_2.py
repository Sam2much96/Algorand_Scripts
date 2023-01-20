#!/usr/bin/env python3

#works

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
from simple_smart_contract import create_app, compile_program, call_app, delete_app, pay, call_app_method
from algosdk.future import transaction

# Create a class, subclassing Application from beaker
class BoxEscrow(Application):

    hashed_secret: Final[ApplicationStateValue] = ApplicationStateValue(
        stack_type=TealType.bytes,
        descr="A scratch for saving secret has to application state",
    )
    
    #store transaction details to  boxes
    
    #ledger = Mapping(abi.Address, abi.Uint64)
    #uses nonce https://www.investopedia.com/terms/n/nonce.asp
    scratch_storage = ScratchVar(TealType.bytes)
    byte_storage = Bytes("owner")  # byteslice

    @Subroutine(TealType.none)  #Bare app calls https://pyteal.readthedocs.io/en/stable/abi.html?highlight=registrable%20methods#registering-bare-app-calls
    def assert_sender_is_creator() -> Expr:
        return Seq(Assert(Txn.sender() == Global.creator_address()))



    # move any balance that the user has into the "lost" amount when they close out or clear state
    transfer_balance_to_lost = App.globalPut(
        Bytes("lost"),
        App.globalGet(Bytes("lost")) + App.localGet(Txn.sender(), Bytes("balance")),
    )


    my_router = Router(
    name="AlgoBank",
    bare_calls=BareCallActions(
        # approve a creation no-op call 
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




            App.box_put(
                sender.address(),
                Bytes("balance"),
                #App.localGet(sender.address(), Bytes("balance")) + payment.get().amount(),
            ),
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

            If(Txn.sender() != Global.creator_address()) #opcode error

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
                )
            .ElseIf( Txn.sender() == Global.creator_address())
            .Then(Approve())
        )



    approval_program, clear_state_program, contract = my_router.compile_program(
        version=8, optimize=OptimizeOptions(scratch_slots=True)
    )







    #testing secrets conversion
    #print (sha256b64("password"))
    with open("algobank_approval.teal", "w") as f:
        f.write(approval_program)

    with open("algobank_clear_state.teal", "w") as f:
        f.write(clear_state_program)
   #     
    with open("algobank.json", "w") as f:
        f.write(json.dumps(contract.dictify(), indent=4))









    


def sha256b64(s: str) -> str:
    return base64.b64encode(hashlib.sha256(str(s).encode("utf-8")).digest()).decode("utf-8")

#running tests on sandbox env
def create_algorand_node_and_acct():
    
    # test-net
    algod_address = "https://node.testnet.algoexplorerapi.io"
    algod_token = ""
    algod_client = algod.AlgodClient(algod_token, algod_address)



    _params = algod_client.suggested_params()

    __mnemonic : str = "tank game arrive train bring taxi tackle popular bacon gasp tell pigeon error step leaf zone suit chest next swim luggage oblige opinion about execute"

    __mnemonic_2 : str = "degree feature waste gospel screen near subject boost wreck proof caution hen adapt fiber fault level blind entry also embark oval board bunker absorb garage"

    #rewrite for testnet
    #client = sandbox.get_algod_client()

    #accts = sandbox.get_accounts()

    accts = {}
    accts[1] = {}
    accts[1]['pk'] = mnemonic.to_public_key(__mnemonic) #saves the new account's address
    accts[1]['sk'] = mnemonic.to_private_key(__mnemonic) #saves the new account's mnemonic
    
    mnemonic_obj_1 = mnemonic.to_private_key(__mnemonic)
    mnemonic_obj_2 = mnemonic.to_public_key(__mnemonic)
    
    #acct = accts.pop()

    print('Algod Client Status: ',algod_client.status())

    print (accts[1])

    #other accounts
    accts[2] = {}
    accts[2]['pk'] = mnemonic.to_public_key(__mnemonic_2)
    accts[2]['sk'] = mnemonic.to_private_key(__mnemonic_2)

    # Create an Application client containing both an algod client and my app
    
    app_client = algod.AlgodClient(algod_token, algod_address,headers={'User-Agent': 'DoYouLoveMe?'})


    print('Algod Client Status: ',algod_client.status())

    _app_id : int = 154830235


    #deploy(_params, accts[1]['sk'],algod_client)

    #delete_app(algod_client, accts[1]['sk'], _app_id)

    #pay(algod_client, accts[2]['sk'], accts[1]['pk'], 1101101)
    
    #SEND A NEW PARAMS FOR APP CALLS


    call_app(algod_client, accts[2]['sk'], _app_id, "withdraw(0,RJ6STB3FL6VNNRSIMA3K5EU4DQIJJ6FAZEOIHQZA7B4GGUNLU4VSXACWYY)void") #use call_app_methode instead #set fee to 2000 Algos

def deploy(_params, mnemonic_ ,algod_client):

    #app_client = ApplicationClient(client=algod_client, app=BoxEscrow(),sender=accts[1]['pk'] ,signer=accts[1]['sk'])

    #secret = sha256b64("password") #XohImNooBHFR0OVvjcYpJ3NgPQ1qq73WKhHvch0VQtg=

    # declare application state storage (immutable)
    local_ints = 0
    local_bytes = 0
    global_ints = 1
    global_bytes = 1
    global_schema = transaction.StateSchema(global_ints, global_bytes)
    local_schema = transaction.StateSchema(local_ints, local_bytes)


    #Modernize this code to Read from the compiled Teal Source

    approval_program = """
#pragma version 8
txn NumAppArgs
int 0
==
bnz main_l8
txna ApplicationArgs 0
method "deposit(pay,account)void"
==
bnz main_l7
txna ApplicationArgs 0
method "getBalance(account)uint64"
==
bnz main_l6
txna ApplicationArgs 0
method "withdraw(uint64,account)void"
==
bnz main_l5
err
main_l5:
txn OnCompletion
int NoOp
==
txn ApplicationID
int 0
!=
&&
assert
txna ApplicationArgs 1
btoi
store 3
txna ApplicationArgs 2
int 0
getbyte
store 4
load 3
load 4
callsub withdraw_3
int 1
return
main_l6:
txn OnCompletion
int NoOp
==
txn ApplicationID
int 0
!=
&&
assert
txna ApplicationArgs 1
int 0
getbyte
callsub getBalance_2
store 2
byte 0x151f7c75
load 2
itob
concat
log
int 1
return
main_l7:
txn OnCompletion
int NoOp
==
txn ApplicationID
int 0
!=
&&
txn OnCompletion
int OptIn
==
txn ApplicationID
int 0
!=
&&
||
assert
txna ApplicationArgs 1
int 0
getbyte
store 1
txn GroupIndex
int 1
-
store 0
load 0
gtxns TypeEnum
int pay
==
assert
load 0
load 1
callsub deposit_1
int 1
return
main_l8:
txn OnCompletion
int NoOp
==
bnz main_l18
txn OnCompletion
int OptIn
==
bnz main_l17
txn OnCompletion
int CloseOut
==
bnz main_l16
txn OnCompletion
int UpdateApplication
==
bnz main_l15
txn OnCompletion
int DeleteApplication
==
bnz main_l14
err
main_l14:
txn ApplicationID
int 0
!=
assert
callsub assertsenderiscreator_0
int 1
return
main_l15:
txn ApplicationID
int 0
!=
assert
callsub assertsenderiscreator_0
int 1
return
main_l16:
txn ApplicationID
int 0
!=
assert
byte "lost"
byte "lost"
app_global_get
txn Sender
byte "balance"
app_local_get
+
app_global_put
int 1
return
main_l17:
int 1
return
main_l18:
txn ApplicationID
int 0
==
assert
int 1
return

// assert_sender_is_creator
assertsenderiscreator_0:
txn Sender
global CreatorAddress
==
assert
retsub

// deposit
deposit_1:
store 6
store 5
load 5
gtxns Sender
load 6
txnas Accounts
==
assert
load 5
gtxns Receiver
global CurrentApplicationAddress
==
assert
load 6
txnas Accounts
byte "balance"
box_put
retsub

// getBalance
getBalance_2:
txnas Accounts
byte "balance"
app_local_get
retsub

// withdraw
withdraw_3:
store 8
store 7
txn Sender
global CreatorAddress
!=
bnz withdraw_3_l3
txn Sender
global CreatorAddress
==
bz withdraw_3_l4
int 1
return
withdraw_3_l3:
itxn_begin
int pay
itxn_field TypeEnum
load 8
txnas Accounts
itxn_field Receiver
load 7
itxn_field Amount
int 1000
itxn_field Fee
itxn_submit
withdraw_3_l4:
retsub
    """
    



    clear_state_program = """
#pragma version 8
txn NumAppArgs
int 0
==
bnz main_l2
err
main_l2:
byte "lost"
byte "lost"
app_global_get
txn Sender
byte "balance"
app_local_get
+
app_global_put
int 1
return
    """

    



    response = algod_client.compile(approval_program)
    print ("Raw Response =",response )
    print("Response Result = ",response['result'])
    print("Response Hash = ",response['hash'])


    # compile program to binary
    approval_program_compiled = compile_program(algod_client, approval_program)

    # compile program to binary
    clear_state_program_compiled = compile_program(algod_client, clear_state_program)


    app_id, app_addr, txid = create_app(algod_client,_params ,mnemonic_, approval_program_compiled, clear_state_program_compiled, global_schema, local_schema)

    # Create the applicatiion on chain, set the app id for the app client & store app secret
    #app_id, app_addr, txid = #app_client.create(sender=mnemonic_obj_2, signer=mnemonic_obj_2)
    
    print(f"Created App with id: {app_id} and address addr: {app_addr} in tx: {txid}")

    #app_client.call(BoxEscrow.withdraw)
    
    #result = app_client.call(BoxEscrow.withdraw, 101_100, accts[2]['pk'])
    
    #print(f"Currrent counter value: {result.return_value}")

    
    #disabling for debugging

    #try:
    #    other_acct = accts.pop()
    #     other_acct = accts[2]

    #     other_client = app_client.prepare(signer=accts[2]['sk'])
    #     other_client.call(BoxEscrow.withdraw, secret)
    #except LogicException as e:
    #    print("App call failed as expected.")
    #    print(e)




if __name__ == "__main__":
    
    #Builds the progam and deploys
    ca = BoxEscrow()
    

    create_algorand_node_and_acct()
    
    #deploy()
    #
