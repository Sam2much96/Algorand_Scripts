#!/usr/bin/env python3

#works

from pyteal import *
from beaker import *

import base64
import hashlib
from base64 import b64encode, b64decode

from typing import Final

#from beaker.lib.storage import Mapping

#beker documentation
#https://algorand-devrel.github.io/beaker/html/application_client.html


from algosdk.v2client import algod
from algosdk import mnemonic
from beaker.client.application_client import ApplicationClient
from beaker.client.logic_error import LogicException
from beaker.consts import Algos

from beaker.lib.storage import Mapping

# Create a class, subclassing Application from beaker
class BoxEscrow(Application):

    hashed_secret: Final[ApplicationStateValue] = ApplicationStateValue(
        stack_type=TealType.bytes,
        descr="A scratch for saving secret has to application state",
    )
    
    #store transaction details to  boxes
    ledger = Mapping(abi.Address, abi.Uint64)
    scratch_box_withd_amt = Mapping(abi.Address, abi.Uint64)
    scratch_box_secrets = Mapping(abi.Address, abi.Byte)

    #scratch_sender = ScratchVar(TealType.bytes)
    #scratch_secret = ScratchVar(TealType.bytes)
    #scratch_withdrawal_amount = ScratchVar(TealType.uint64)
    #scratch_nonce = ScratchVar(TealType.uint64) #uses nonce https://www.investopedia.com/terms/n/nonce.asp


    @create(authorize=Authorize.only(Global.creator_address()))
    def create(self, secret):
        self.hashed_secret = Bytes("base64", secret) # The first argument should be the hashed secret
        self.initialize_application_state()

        #write to box using opcode
        # 100 byte box created with box_create
        App.box_create("scratch_box_withd_amt",Int(100))

        

    @opt_in
    def opt_in(self):
        return Approve()

    @no_op
    def withdraw(self):

        return Seq(
                [
                    # If App call has more than 1 Argument
                    If (Txn.application_args.length() > Int(1)), {
                
                    #store the Txn variables to scratch variables
                    self.scratch_box_secrets[Txn.sender(),Txn.application_args[1] ], #stores secrets
                    self.scratch_box_withd_amt[Txn.sender(),Txn.application_args[2] ], #stores withdrawal amt
                    #self.scratch_secret.store(Txn.application_args[1]), # the 2nd app arg
                    #self.scratch_withdrawal_amount.store(Btoi(Txn.application_args[2])), # the 3rd app arg

                        
                    },

                    #load from box
                    #box_str := App.box_get(Bytes(str(Txn.sender())),

                    #asset that it isn't null
                    #Assert( box_str.hasValue()),

                        # Compare secrets
                    Assert((self.compare_secret(Txn.application_args[1]))) ,

                        #make sure the smartcontract has funds to payout
                    And(Assert(get_balance(Global.creator_address()) >= self.scratch_box_withd_amt.box_get(Txn.sender()))),
                    Then(
                            # Pay out the withdrawal amount to the sender
                            payout(Txn.sender(), self.scratch_box_withd_amt.get(Txn.sender())),
                       
                            #save Txn Details to Box Ledger
                            #self.ledger[Txn.sender()].set(Itob(scratch_box_withd_amt.get(Txn.sender()))),
                            Approve()
                        ),
                    Else (
                            Reject()

                        )
                ]
                )

    @Subroutine(TealType.uint64)
    def compare_secret(scratch_secret ) -> Expr:
        return Seq(Approve() if self.hashed_secret == scratch_secret else Reject())


        #Store to receivers address to a Box

    #deletes the app
    @delete(authorize=Authorize.only(Global.creator_address()))
    def delete():
        return Approve()
        
    
    #https://pyteal.readthedocs.io/en/stable/api.html?highlight=delete%20application#pyteal.BareCallActions.delete_application
    #Updates the app  
    @update(authorize=Authorize.only(Global.creator_address()))
    def update():
        return Approve()

    #should only withdraw if the Address has some Algos
    @Subroutine(TealType.uint64)
    def get_balance(self) -> Expr: 
        balanceint : uint64=  App.balance(Global.creator_address())
        return balanceint



    #construct a payment txn
    #https://developer.algorand.org/docs/get-details/dapps/smart-contracts/apps/
    @Subroutine(TealType.anytype)
    def payout(scratch_sender, scratch_withdrawal_amount):
        return Seq(
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields({
            TxnField.type_enum: TxnType.Payment,
            TxnField.amount: Algos(scratch_withdrawal_amount.load()), 
            TxnField.receiver: scratch_sender.load() 
            }),
        InnerTxnBuilder.Submit(),
        )



def sha256b64(s: str) -> str:
    return base64.b64encode(hashlib.sha256(str(s).encode("utf-8")).digest()).decode("utf-8")

#running tests on sandbox env
def demo():
    
    # test-net
    algod_address = "https://node.testnet.algoexplorerapi.io"
    algod_token = ""
    algod_client = algod.AlgodClient(algod_token, algod_address)



    params = algod_client.suggested_params()

    __mnemonic : str = "tank game arrive train bring taxi tackle popular bacon gasp tell pigeon error step leaf zone suit chest next swim luggage oblige opinion about execute"

    __mnemonic_2 : str = "degree feature waste gospel screen near subject boost wreck proof caution hen adapt fiber fault level blind entry also embark oval board bunker absorb garage"

    #rewrite for testnet
    #client = sandbox.get_algod_client()

    #accts = sandbox.get_accounts()

    accts = {}
    accts[1] = {}
    accts[1]['pk'] = mnemonic.to_public_key(__mnemonic_2) #saves the new account's address
    accts[1]['sk'] = mnemonic.to_private_key(__mnemonic) #saves the new account's mnemonic
    #acct = accts.pop()

    #other accounts
    accts[2] = {}
    accts[2]['pk'] = mnemonic.to_public_key(__mnemonic_2)
    accts[2]['sk'] = mnemonic.to_private_key(__mnemonic_2)

    # Create an Application client containing both an algod client and my app
    app_client = ApplicationClient(client=algod_client, app=BoxEscrow(), signer=accounts[1]['pk'], params=params)

    secret = sha256b64("password") #XohImNooBHFR0OVvjcYpJ3NgPQ1qq73WKhHvch0VQtg=

    # Create the applicatiion on chain, set the app id for the app client & store app secret
    app_id, app_addr, txid = app_client.create(args=secret)
    
    print(f"Created App with id: {app_id} and address addr: {app_addr} in tx: {txid}")

    #app_client.call(BoxEscrow.withdraw)
    
    result = app_client.call(BoxEscrow.withdraw, secret)
    
    print(f"Currrent counter value: {result.return_value}")

    
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
    
    #runs the progam and the demo
    ca = BoxEscrow()
    demo()


    #testing secrets conversion
    #print (sha256b64("password"))
