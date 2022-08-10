# rock paper scissors smart contract
from pyteal import *
from pyteal.ast.bytes import Bytes
from pyteal_helpers import program

def approval(): # Uses local storage, not global storage
    #locals
    local_opponent = Bytes("opponent")  #Byteslice #would store opponent account address
    local_wager = Bytes("wager") #uint64
    local_commitment = Bytes("commitment") #Byteslice #hashed play
    local_reveal = Bytes("reveal") #byteslice #unhashed play 

    #operations
    op_challenge = Bytes("challenge")
    op_accept = Bytes("accept")
    op_reveal = Bytes("reveal")
    
    @Subroutine (Tealtype.none) #subroutines allows code reusablility in teal. This subroutine returns nothing
    def reset( account : Expr):
        return Seq(
            App.localPut(account, local_opponent , Bytes("")),
            App.localPut(account, local_wager , Int(0)),
            App.localPut(account, local_commitment , Bytes("")),
            App.localPut(account, local_reveal , Bytes("")),
        )

    @Subroutine (Tealtype.none)
    def create_challenge():
        return Reject()
    
    @Subroutine (Tealtype.none)
    def accept_challenge():
        return Reject()

    @Subroutine (Tealtype.none)
    def create_challenge():
        return reveal()

    return program.event (
        init=Approve(),
        opt_in = Seq (
            reset(Int(0)),
            Approve(),
        ),

        no_op=Seq(
            Cond(
                [Txn.application_args[0] == op_challenge, create_challenge()]
                [Txn.application_args[0] == op_accept, accept_challenge()]
                [Txn.application_args[0] == op_reveal, reveal()]
            ),
            Reject(),
        ),

    )
    

def clear():
    return Approve()