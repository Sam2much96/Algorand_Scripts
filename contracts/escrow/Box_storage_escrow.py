#!/usr/bin/env python3

#Escrow Withdrawal SmartContract
# Using Box Storage & Beaker
# Is currently a voting Dapp + an escrow withdrawal dap

from pyteal import *
from beaker import *
from algosdk.atomic_transaction_composer import AccountTransactionSigner
from algosdk.account import generate_account
from algosdk.encoding import decode_address


from beaker.lib.storage import Mapping

import os

from typing import List




class Vote(Application):
    proposal = ApplicationStateValue(stack_type=TealType.bytes)

    @create
    def create(self):
        return Seq(self.proposal.set(Bytes("Buy NFTs?")), Approve())

    @opt_in
    def opt_in(self):
        return Approve()

    @external
    def submit_vote(self, vote: abi.Bool):
        return Reject()


def submit_votes(app):
    app_class = app.__class__.__name__
    
    #modify for testnet
    creator = sandbox.get_accounts()[0]
    app_client = client.ApplicationClient(
        client=sandbox.get_algod_client(),
        app=app,
        sender=creator.address,
        signer=creator.signer,
    )
    app_client.create()

    print(app_client.app_id)


#remove unnecessay code from this bloc
    try:
        addrs = []

        #creates random accounts
        for _ in range(100):
            [sk, addr] = generate_account()
            addrs.append(addr)
            signer = AccountTransactionSigner(sk)



            # Logic for Class Type

            if app_class == "LocalVote":
                # Fund the account with account MBR, fee, and MBR needed for opting in
                app_client.fund(230_500, addr)

                # Opt into app
                app_client.opt_in(sender=addr, signer=signer)
            elif app_class == "BoxVote":
                # Fund account with account MBR and fee
                app_client.fund(101_000, addr)

                # Fund contract with box MBR
                app_client.fund(118500)
            elif app_class == "GlobalVote":
                # Fund account with account MBR and fee
                app_client.fund(101_000, addr)

            app_client.call(
                method=app.submit_vote,
                vote=True,
                sender=addr,
                signer=signer,
                boxes=[(app_client.app_id, decode_address(addr))],
            )

    #Debugs Storage State on SmartContracts
    #finally:
    #    if app_class == "GlobalVote":
    #        print(app_client.get_application_state())
     #   elif app_class == "LocalVote":
            # We must know all of the addresses to get all of the votes
      #      for a in addrs:
      #          print(f"{a}: {app_client.get_account_state(addr)}")
        if app_class == "BoxVote":
            for box in app_client.get_box_names():
                print(f"{box}: {app_client.get_box_contents(box)}")






class BoxVote(Vote):
    votes = Mapping(abi.Address, abi.Bool)

    @external
    def submit_vote(self, vote: abi.Bool):
        return Seq(self.votes[Txn.sender()].set(Itob(vote.get())), Approve())


if __name__ == "__main__":
    if os.path.exists("box.teal"):
        os.remove("box.teal")

    app = BoxVote(version=8)

    with open("box.teal", "w") as f:
        f.write(app.approval_program)

    submit_votes(BoxVote(version=8))




def approval(
    owner_address: Expr,
    beneficiary_address: Expr,
    hashed_secret: Expr,
    unlock_at_round: Expr,
):
    return Return(
        And(
            # check fee
            Txn.fee() <= Global.min_txn_fee() * Int(2),
            # check payment parameters
            Txn.type_enum() == TxnType.Payment,
            Txn.close_remainder_to() == Global.zero_address(),
            Txn.rekey_to() == Global.zero_address(),
            # check recipient
            Or(
                # beneficiary unlocks with secret key
                And(
                    Txn.receiver() == beneficiary_address,
                    Sha256(Arg(0)) == hashed_secret,
                ),
                # expiration time passes and funds return to owner
                And(
                    Txn.receiver() == owner_address,
                    Txn.first_valid() >= unlock_at_round,
                ),
            ),
        ),
    )


def create(args: List[str]) -> str:

    owner_address = Addr(args[0])
    beneficiary_address = Addr(args[1])
    hashed_secret = Bytes("base64", sha256b64(args[2]))
    unlock_at_round = Int(int(args[3]))

    return approval(
        owner_address,
        beneficiary_address,
        hashed_secret,
        unlock_at_round,
    )



#https://developer.algorand.org/articles/smart-contract-storage-boxes/
def create_box():
    # 100 byte box created with box_create
    app_client.box_create(“MyKey”,Int(100))
    …
    # box created with box_put
    app_client.box_put(“MyKey”, “My data values”)

